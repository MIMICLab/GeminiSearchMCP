"""Web search helper backed by Gemini and Google Search grounding."""

from __future__ import annotations

from google import genai
from google.genai import types

from .config import WEB_SEARCH_MODEL
from .google_client import GeminiClientError, get_gemini_client


def run_web_search(query: str) -> str:
    """Run a grounded web search query via Gemini."""
    if not query.strip():
        raise ValueError("Search query must not be empty")
    try:
        client: genai.Client = get_gemini_client()
    except GeminiClientError as exc:
        raise RuntimeError(str(exc)) from exc

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    response = client.models.generate_content(
        model=WEB_SEARCH_MODEL,
        contents=query,
        config=config,
    )

    text = getattr(response, "text", "") or ""
    if not text.strip():
        return "(no answer returned)"
    return text.strip()


__all__ = ["run_web_search"]
