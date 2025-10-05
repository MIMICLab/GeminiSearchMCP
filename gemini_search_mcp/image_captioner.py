"""Image captioning utilities backed by Gemini vision models."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from google.genai import types

from .config import VISION_MODEL
from .google_client import GeminiClientError, get_gemini_client

DEFAULT_PROMPT = "Describe the image in detail so a reader can understand it without seeing it."


@dataclass(slots=True)
class ImageCaptionRequest:
    """Represents a single image caption request."""

    image_path: Path
    prompt: str | None = None


def _detect_mime(path: Path) -> str:
    guess = mimetypes.guess_type(path.name)[0]
    return guess or "image/png"


def caption_images(
    requests: Iterable[ImageCaptionRequest],
    *,
    model: str | None = None,
) -> dict[Path, str]:
    """Generate captions for images using Gemini vision models."""
    buffered = [r for r in requests if r.image_path.exists()]
    if not buffered:
        return {}
    try:
        client = get_gemini_client()
    except GeminiClientError:
        return {}
    results: dict[Path, str] = {}
    for request in buffered:
        try:
            payload = request.image_path.read_bytes()
        except OSError:
            continue
        prompt = request.prompt or DEFAULT_PROMPT
        try:
            response = client.models.generate_content(
                model=model or VISION_MODEL,
                contents=[
                    types.Part.from_text(prompt),
                    types.Part.from_bytes(payload, mime_type=_detect_mime(request.image_path)),
                ],
            )
        except Exception:
            continue
        text = getattr(response, "text", "") or ""
        if text.strip():
            results[request.image_path] = text.strip()
    return results


__all__ = ["ImageCaptionRequest", "caption_images", "DEFAULT_PROMPT"]
