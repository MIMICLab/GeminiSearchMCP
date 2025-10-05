"""Rewrite markdown images into inline captions."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable

from .config import CACHE_DIR
from .image_captioner import ImageCaptionRequest, caption_images

CAPTION_START_MARKER = "<!---MEDIA CAPTION STARTS --->"
CAPTION_END_MARKER = "<!---MEDIA CAPTION ENDS --->"
_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)")


def _normalize_markdown(text: str) -> str:
    lines = text.splitlines()
    normalized = "\n".join(line.rstrip() for line in lines)
    if lines:
        normalized += "\n"
    return normalized


def _resolve_media_path(ref: str, base: Path) -> Path | None:
    candidate = (base / ref).resolve()
    return candidate if candidate.exists() else None


def rewrite_markdown_with_captions(
    source_markdown: Path,
    target_path: Path,
    source_hash: str,
    *,
    vision_model: str | None = None,
    disable_cache: bool = False,
    clear_cache: bool = False,
) -> list[dict]:
    raw = source_markdown.read_text(encoding="utf-8")
    matches = list(_IMAGE_PATTERN.finditer(raw))
    if not matches:
        normalized = _normalize_markdown(raw)
        target_path.write_text(normalized, encoding="utf-8")
        return []

    assets: list[dict] = []
    replacements: dict[tuple[int, int], str] = {}
    requests: list[ImageCaptionRequest] = []
    lookup: dict[Path, tuple[tuple[int, int], dict]] = {}

    for index, match in enumerate(matches):
        span = match.span()
        alt = (match.group("alt") or "").strip()
        ref = match.group("path").strip()
        resolved = _resolve_media_path(ref, source_markdown.parent)
        asset_id = f"{source_hash}_img_{index:03d}"
        asset = {
            "id": asset_id,
            "source_file": str(resolved or ref),
            "caption": alt,
        }
        assets.append(asset)
        replacements[span] = alt or ref
        if resolved is not None:
            request = ImageCaptionRequest(resolved)
            requests.append(request)
            lookup[resolved] = (span, asset)

    cache_entries: dict[str, str] = {}
    cache_path = CACHE_DIR / "caption_cache.json"
    if clear_cache and cache_path.exists():
        cache_path.unlink()
    if not disable_cache and cache_path.exists():
        try:
            cache_entries = json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cache_entries = {}

    pending: list[ImageCaptionRequest] = []
    for request in requests:
        item = lookup.get(request.image_path)
        if not item:
            continue
        span, asset = item
        try:
            blob = request.image_path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha1(blob).hexdigest()
        cache_key = f"{vision_model or ''}:{digest}"
        cached = None if disable_cache else cache_entries.get(cache_key)
        if cached:
            replacements[span] = cached
            asset["caption"] = cached
            continue
        pending.append(request)
        asset["cache_key"] = cache_key
        asset["span"] = span

    if pending:
        captions = caption_images(pending, model=vision_model)
        for path, text in captions.items():
            item = lookup.get(path)
            if not item:
                continue
            span, asset = item
            cleaned = text.strip()
            if not cleaned:
                continue
            replacements[span] = cleaned
            asset["caption"] = cleaned
            cache_key = asset.pop("cache_key", None)
            if cache_key:
                cache_entries[cache_key] = cleaned

    if not disable_cache and cache_entries:
        try:
            cache_path.write_text(json.dumps(cache_entries, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    pieces: list[str] = []
    cursor = 0
    for span, replacement in sorted(replacements.items(), key=lambda item: item[0]):
        start, end = span
        pieces.append(raw[cursor:start])
        wrapped = f"{CAPTION_START_MARKER} {replacement.strip()} {CAPTION_END_MARKER}"
        pieces.append(wrapped)
        cursor = end
    pieces.append(raw[cursor:])

    normalized = _normalize_markdown("".join(pieces))
    target_path.write_text(normalized, encoding="utf-8")
    for asset in assets:
        asset.pop("span", None)
        asset.pop("cache_key", None)
    return assets


__all__ = ["rewrite_markdown_with_captions", "CAPTION_START_MARKER", "CAPTION_END_MARKER"]
