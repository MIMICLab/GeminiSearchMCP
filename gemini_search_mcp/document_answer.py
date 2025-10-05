"""Answer generation using Gemini from processed markdown."""

from __future__ import annotations

from google import genai
from google.genai import types

from .config import DEFAULT_MODEL
from .google_client import GeminiClientError, get_gemini_client

ANSWER_MODEL = "gemini-2.5-flash"


def generate_answer(question: str, markdown: str) -> str:
    if not question.strip():
        raise ValueError("Question must not be empty")
    if not markdown.strip():
        raise ValueError("Markdown content required for answer generation")
    try:
        client: genai.Client = get_gemini_client()
    except GeminiClientError as exc:
        raise RuntimeError(str(exc)) from exc

    model = ANSWER_MODEL or DEFAULT_MODEL
    response = client.models.generate_content(
        model=model,
        contents=[
            f"You are a helpful assistant. Use the following markdown to answer the question.\n\n"
            f"Markdown:\n{markdown}\n\nQuestion: {question}\n",
        ],
        config=types.GenerateContentConfig(
            temperature=0.1
        )
    )
    text = getattr(response, "text", "") or ""
    if text.strip():
        return text.strip()
    return "(no answer generated)"


__all__ = ["generate_answer", "ANSWER_MODEL", "DEFAULT_MODEL"]
