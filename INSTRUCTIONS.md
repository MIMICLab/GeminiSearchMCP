# Gemini Search MCP Server - Build Instructions

## Overview
Build a simple MCP server that allows clients to use Gemini API as a search engine.

## Requirements

### 1. Default Model
- Use `gemini-2.5-flash-lite` as the default model

### 2. Web Search Support
Implement web search using Google Search grounding:

```python
from google import genai
from google.genai import types

client = genai.Client()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Who won the euro 2024?",
    config=config,
)

print(response.text)
```

### 3. Document-Based Search
Support document-based search with the following pipeline:

#### 3.1 PDF Converter
Convert any document to PDF using the provided `pdf_converter.py` code.

#### 3.2 Markdown Converter
Convert PDF from 3.1 to markdown using the provided `converter_runner.py` code.

#### 3.3 Markdown Rewriter
Rewrite markdown by converting image paths with captions using the provided `markdown_rewriter.py` code.

#### 3.4 Image Captioner
Generate captions for images using the provided `image_captioner.py` code.

#### 3.5 Answer Generation
Give answer to client's question based on final markdown using Gemini:

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=["Explain how AI works"],
    config=types.GenerateContentConfig(
        temperature=0.1
    )
)
print(response.text)
```

**Important**: 
- Set reasonable temperature (0.1) for accurate answers
- Include full markdown content in the prompt

## Implementation Notes
- Use exact code snippets provided for each component
- Maintain the dependency chain: document → PDF → markdown → captioned markdown → answer
- Handle caching appropriately for performance
