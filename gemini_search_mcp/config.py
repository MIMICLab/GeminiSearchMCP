"""Configuration helpers for the Gemini Search MCP server."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash-lite"
WEB_SEARCH_MODEL = "gemini-2.5-flash"
VISION_MODEL = os.environ.get("GEMINI_VISION_MODEL", "gemini-2.5-flash-lite")
CACHE_DIR = Path(os.environ.get("GEMINI_MCP_CACHE", Path.home() / ".cache" / "gemini_search_mcp"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GOOGLE_API_KEY_ENV = "GOOGLE_API_KEY"

__all__ = [
    "DEFAULT_MODEL",
    "WEB_SEARCH_MODEL",
    "VISION_MODEL",
    "CACHE_DIR",
    "GOOGLE_API_KEY_ENV",
]
