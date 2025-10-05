"""Entry point for the Gemini Search MCP server."""

from __future__ import annotations

import asyncio
from typing import Annotated
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
        f"Default model: {DEFAULT_MODEL}."
    ),
)

_pipeline = DocumentPipeline()


@mcp.tool(
    name="web_search",
    description="Run a Google-grounded web search via Gemini and return the answer text.",
)
async def tool_web_search(
    query: Annotated[str, Field(description="Search query to send to Gemini web search tool.")],
    context: Context | None = None,
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
    context: Context | None = None,
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


def run() -> None:
    """Run the MCP server using stdio transport."""
    mcp.run("stdio")


if __name__ == "__main__":
    run()
