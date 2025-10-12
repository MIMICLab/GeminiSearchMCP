"""Entry point for the Gemini Search MCP server."""

import asyncio
from typing import Annotated, Optional
from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from .config import DEFAULT_MODEL
from .document_answer import generate_answer
from .document_pipeline import DocumentPipeline
from .web_search import run_web_search

mcp = FastMCP(
    name="gemini-search-mcp",
    instructions=(
        "Use Gemini to run grounded web searches and answer questions about documents. "
        f"Default model: {DEFAULT_MODEL}. "
        "Available tools: web_search, document_question_answering, get_document_content, get_document_chunk, get_next_chunk."
    ),
)

_pipeline = DocumentPipeline()

# Session state: track current document being read
_current_document: Optional[str] = None
_current_chunk_index: int = 0
_current_chunk_size: int = 10000


@mcp.tool(
    name="web_search",
    description="Run a Google-grounded web search via Gemini and return the answer text.",
)
async def tool_web_search(
    query: Annotated[str, Field(description="Search query to send to Gemini web search tool.")],
    context: Context = None,
) -> str:
    if context is not None:
        await context.info(f"Starting web search for query: {query}")
    result = run_web_search(query)
    if context is not None:
        await context.info("Web search completed")
    return result


@mcp.tool(
    name="document_question_answering",
    description="Answer a question about a document by converting it to markdown and using Gemini.",
)
async def tool_document_question_answering(
    document_path: Annotated[str, Field(description="Path to the document to analyze.")],
    question: Annotated[str, Field(description="Question to answer using the document content.")],
    context: Context = None,
) -> str:
    path = document_path
    if context is not None:
        await context.info(f"Processing document at {path}")
    processed = await asyncio.to_thread(_pipeline.process, Path(path))
    if context is not None:
        await context.info("Document processed; invoking Gemini for answer generation")
    answer = await asyncio.to_thread(generate_answer, question, processed.markdown_text)
    if context is not None:
        await context.info("Answer generation complete")
    return answer


@mcp.tool(
    name="get_document_content",
    description="Convert a document to markdown and return its full content. Useful for reading entire documents.",
)
async def tool_get_document_content(
    document_path: Annotated[str, Field(description="Path to the document to convert and read.")],
    include_images: Annotated[bool, Field(description="Whether to include image descriptions in the output.")] = True,
    context: Context = None,
) -> str:
    """
    Convert and return the full markdown content of a document.
    Supports PDF, images, Office documents, and more.
    Also sets this as the current document for use with get_next_chunk.
    """
    global _current_document, _current_chunk_index, _current_chunk_size
    
    path = document_path
    if context is not None:
        await context.info(f"Converting document at {path}")
    
    processed = await asyncio.to_thread(_pipeline.process, Path(path))
    
    # Save state - reset to start of document
    _current_document = str(Path(path).resolve())
    _current_chunk_index = -1  # -1 means full document was shown
    _current_chunk_size = 10000
    
    if context is not None:
        await context.info("Document conversion complete")
    
    # Return the markdown content
    content = processed.markdown_text
    
    # Add metadata header with file locations
    result = f"# Document: {Path(path).name}\n\n"
    result += f"**Source**: `{path}`\n"
    result += f"**Converted to Markdown**\n\n"
    result += f"**Cached Files**:\n"
    result += f"- Original Markdown: `{processed.markdown_path}`\n"
    result += f"- Rewritten Markdown (with captions): `{processed.rewritten_markdown_path}`\n"
    if processed.pdf_path != processed.source_path:
        result += f"- Converted PDF: `{processed.pdf_path}`\n"
    result += "\n"
    result += "---\n\n"
    result += content
    
    if context is not None:
        char_count = len(content)
        word_count = len(content.split())
        await context.info(f"Retrieved {char_count} characters, ~{word_count} words")
    
    return result


@mcp.tool(
    name="get_document_chunk",
    description="Get a specific chunk (page/section) of a document. Useful for large documents to retrieve content in parts.",
)
async def tool_get_document_chunk(
    document_path: Annotated[str, Field(description="Path to the document to read.")],
    chunk_index: Annotated[int, Field(description="Chunk number to retrieve (0-based index).", ge=0)] = 0,
    chunk_size: Annotated[int, Field(description="Approximate size of each chunk in characters.", ge=1000)] = 10000,
    context: Context = None,
) -> str:
    """
    Get a specific chunk of a document's content.
    Returns the requested chunk along with metadata about total chunks.
    Automatically saves the document path and position for use with get_next_chunk.
    """
    global _current_document, _current_chunk_index, _current_chunk_size
    
    path = document_path
    if context is not None:
        await context.info(f"Converting document at {path}")
    
    processed = await asyncio.to_thread(_pipeline.process, Path(path))
    content = processed.markdown_text
    
    # Save state for next chunk
    _current_document = str(Path(path).resolve())
    _current_chunk_index = chunk_index
    _current_chunk_size = chunk_size
    
    # Split content into chunks
    total_length = len(content)
    start_pos = chunk_index * chunk_size
    end_pos = start_pos + chunk_size
    
    if start_pos >= total_length:
        return f"Error: Chunk {chunk_index} does not exist. Document has {(total_length + chunk_size - 1) // chunk_size} chunks."
    
    chunk_content = content[start_pos:end_pos]
    total_chunks = (total_length + chunk_size - 1) // chunk_size
    
    # Build response with metadata and file locations
    result = f"# Document: {Path(path).name} (Chunk {chunk_index + 1}/{total_chunks})\n\n"
    result += f"**Source**: `{path}`\n"
    result += f"**Chunk**: {chunk_index + 1} of {total_chunks}\n"
    result += f"**Position**: Characters {start_pos:,} - {min(end_pos, total_length):,} of {total_length:,}\n\n"
    result += f"**Cached Files**:\n"
    result += f"- Original Markdown: `{processed.markdown_path}`\n"
    result += f"- Rewritten Markdown (with captions): `{processed.rewritten_markdown_path}`\n"
    if processed.pdf_path != processed.source_path:
        result += f"- Converted PDF: `{processed.pdf_path}`\n"
    result += "\n"
    result += "---\n\n"
    result += chunk_content
    
    if end_pos < total_length:
        result += f"\n\n---\n\n*Note: More content available. Use `get_next_chunk` to continue, or `get_document_chunk` with chunk_index={chunk_index + 1}.*"
    
    if context is not None:
        await context.info(f"Retrieved chunk {chunk_index + 1}/{total_chunks} ({len(chunk_content)} characters)")
    
    return result


@mcp.tool(
    name="get_next_chunk",
    description="Get the next chunk of the currently reading document. Continues from where the last chunk left off.",
)
async def tool_get_next_chunk(
    context: Context = None,
) -> str:
    """
    Get the next chunk of the document you're currently reading.
    This tool remembers which document you were reading and automatically gets the next part.
    """
    global _current_document, _current_chunk_index, _current_chunk_size
    
    if _current_document is None:
        return "Error: No document is currently being read. Please use `get_document_chunk` first to start reading a document."
    
    # Get next chunk
    next_chunk_index = _current_chunk_index + 1
    
    if context is not None:
        await context.info(f"Getting next chunk (#{next_chunk_index + 1}) of {Path(_current_document).name}")
    
    # Use get_document_chunk with next index
    return await tool_get_document_chunk(
        document_path=_current_document,
        chunk_index=next_chunk_index,
        chunk_size=_current_chunk_size,
        context=context,
    )


def run() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run("stdio")


if __name__ == "__main__":
    run()
