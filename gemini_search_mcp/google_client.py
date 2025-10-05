"""Helpers for constructing Gemini API clients."""

from __future__ import annotations

import functools
import os
from typing import Any

from google import genai

from .config import GOOGLE_API_KEY_ENV


class GeminiClientError(RuntimeError):
    """Raised when a Gemini client cannot be constructed."""


@functools.lru_cache(maxsize=1)
def get_gemini_client(**kwargs: Any) -> genai.Client:
    api_key = kwargs.pop("api_key", None) or os.environ.get(GOOGLE_API_KEY_ENV)
    if not api_key:
        raise GeminiClientError(
            f"Google API key missing; set {GOOGLE_API_KEY_ENV} or pass api_key explicitly"
        )
    return genai.Client(api_key=api_key, **kwargs)


__all__ = ["get_gemini_client", "GeminiClientError"]
