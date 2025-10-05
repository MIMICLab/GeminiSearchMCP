"""Wrappers for image captioning using configured vision services."""
from __future__ import annotations

import logging
from typing import Iterable

from app.services import (
    DEFAULT_VISION_CAPTION_PROMPT,
    GeminiVisionService,
    ImageCaptionRequest,
    VisionService,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT = DEFAULT_VISION_CAPTION_PROMPT


def caption_images(
    requests: Iterable[ImageCaptionRequest],
    *,
    model: str | None = None,
    vision_service: VisionService | None = None,
) -> dict:
    """Return captions keyed by image path using the provided service."""
    buffered = list(requests)
    if not buffered:
        return {}
    service = vision_service or GeminiVisionService(model=model)
    LOGGER.info("Captioning %d image(s) via %s", len(buffered), service.__class__.__name__)
    return service.caption_images(buffered)


__all__ = ["ImageCaptionRequest", "caption_images", "DEFAULT_PROMPT"]
