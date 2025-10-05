"""Utilities to replace markdown image tags with inline captions."""
from __future__ import annotations

import logging
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

from .image_captioner import ImageCaptionRequest, caption_images

LOGGER = logging.getLogger(__name__)

CAPTION_START_MARKER = "<!---MEDIA CAPTION STARTS --->"
CAPTION_END_MARKER = "<!---MEDIA CAPTION ENDS --->"


@dataclass(frozen=True)
class _ImageTag:
    start: int
    end: int
    alt_text: str
    destination: str


def rewrite_markdown_with_captions(
    source_markdown: Path,
    target_path: Path,
    source_hash: str,
    *,
    vision_model: str | None = None,
    disable_cache: bool = True,
    clear_cache: bool = False,
) -> list[dict]:
    """Rewrite markdown by replacing image tags with caption text.

    Returns the collected media asset metadata for downstream bookkeeping.
    """

    raw_text = source_markdown.read_text(encoding="utf-8")
    tags = _find_image_tags(raw_text)

    if not tags:
        normalized = _normalize_markdown(raw_text)
        target_path.write_text(normalized, encoding="utf-8")
        return []

    entries: list[dict] = []
    for tag in tags:
        alt = tag.alt_text.strip()
        resolved = _resolve_image_path(tag.destination, source_markdown.parent)
        if resolved is None and tag.destination:
            LOGGER.warning("Image referenced in markdown not found: %s", tag.destination)
        fallback = alt or Path(unquote(tag.destination)).stem or "[이미지]"
        entries.append(
            {
                "span": (tag.start, tag.end),
                "alt": alt,
                "raw_path": tag.destination,
                "resolved": resolved,
                "fallback": fallback or "[이미지]",
            }
        )

    targets: list[dict] = []
    lookup: dict[str, dict] = {}
    for entry in entries:
        resolved = entry["resolved"]
        raw_path = entry["raw_path"]
        key = _make_target_key(resolved, raw_path)
        bucket = lookup.get(key)
        if bucket is None:
            asset_id = f"{source_hash}_img_{len(targets):03d}"
            bucket = {
                "id": asset_id,
                "resolved": resolved,
                "raw_path": raw_path,
                "alts": [],
            }
            lookup[key] = bucket
            targets.append(bucket)
        bucket["alts"].append(entry.get("alt", ""))
        entry["asset_id"] = bucket["id"]

    # Use corpus root as cache location: <output_dir>/media_captions.json
    # where target_path is typically <output_dir>/markdown/<hash>.md
    try:
        corpus_root = target_path.parent.parent
    except Exception:
        corpus_root = target_path.parent
    caption_lookup = _generate_caption_lookup(
        targets,
        vision_model=vision_model,
        cache_root=corpus_root,
        disable_cache=disable_cache,
        clear_cache=clear_cache,
    )
    for bucket in targets:
        caption = caption_lookup.get(bucket["id"]) or _fallback_caption(bucket)
        bucket["caption"] = caption if caption.strip() else "[이미지]"

    caption_by_asset = {bucket["id"]: bucket["caption"] for bucket in targets}
    parts: list[str] = []
    cursor = 0
    for entry in entries:
        start, end = entry["span"]
        parts.append(raw_text[cursor:start])
        replacement = caption_by_asset.get(entry["asset_id"], entry["fallback"])
        replacement = replacement if replacement.strip() else entry["fallback"]
        core = replacement.strip() if replacement else entry["fallback"]
        wrapped = f"{CAPTION_START_MARKER} {core} {CAPTION_END_MARKER}"
        parts.append(wrapped)
        cursor = end
    parts.append(raw_text[cursor:])

    processed = "".join(parts)
    normalized = _normalize_markdown(processed)
    target_path.write_text(normalized, encoding="utf-8")

    media_assets: list[dict] = []
    for bucket in targets:
        source_file = bucket["resolved"] if bucket["resolved"] else Path(unquote(bucket["raw_path"]))
        media_assets.append(
            {
                "id": bucket["id"],
                "source_file": str(source_file),
                "caption": bucket["caption"],
            }
        )
    return media_assets


def _normalize_markdown(text: str) -> str:
    lines = text.splitlines()
    normalized_lines = [line.rstrip() for line in lines]
    normalized = "\n".join(normalized_lines)
    if lines:
        normalized += "\n"
    return normalized


def _find_image_tags(text: str) -> list[_ImageTag]:
    tags: list[_ImageTag] = []
    idx = 0
    length = len(text)
    while idx < length:
        start = text.find("![", idx)
        if start == -1:
            break
        alt_start = start + 2
        alt_end = _find_closing_bracket(text, alt_start)
        if alt_end == -1:
            break
        if alt_end + 1 >= length or text[alt_end + 1] != "(":
            idx = alt_end + 1
            continue
        dest_start = alt_end + 2
        dest_end = _find_matching_paren(text, dest_start)
        if dest_end == -1:
            idx = alt_end + 1
            continue
        raw_destination = text[dest_start:dest_end]
        destination = _extract_destination(raw_destination)
        alt_text = text[alt_start:alt_end]
        tags.append(
            _ImageTag(
                start=start,
                end=dest_end + 1,
                alt_text=alt_text,
                destination=destination,
            )
        )
        idx = dest_end + 1
    return tags


def _find_closing_bracket(text: str, start: int) -> int:
    i = start
    length = len(text)
    while i < length:
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "]":
            return i
        i += 1
    return -1


def _find_matching_paren(text: str, start: int) -> int:
    i = start
    length = len(text)
    depth = 1
    while i < length:
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _extract_destination(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("<"):
        closing = cleaned.find(">")
        if closing != -1:
            return cleaned[1:closing]
    buffer: list[str] = []
    escape = False
    for char in cleaned:
        if escape:
            buffer.append(char)
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char.isspace():
            break
        buffer.append(char)
    return "".join(buffer)


def _resolve_image_path(raw_path: str, root_dir: Path) -> Path | None:
    cleaned = unquote(raw_path.strip())
    if not cleaned:
        return None

    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1]

    candidate = (root_dir / cleaned).resolve()
    try:
        candidate.relative_to(root_dir.resolve())
    except ValueError:
        candidate = None
    if candidate and candidate.exists():
        return candidate

    direct = Path(cleaned)
    if direct.is_absolute() and direct.exists():
        return direct

    fallback_name = Path(cleaned).name
    for match in root_dir.rglob(fallback_name):
        if match.is_file():
            return match
    return None


def _make_target_key(resolved: Path | None, raw_path: str) -> str:
    if resolved is not None:
        try:
            return resolved.resolve().as_posix()
        except OSError:
            return str(resolved)
    return raw_path


def _generate_caption_lookup(
    targets: list[dict],
    *,
    vision_model: str | None = None,
    cache_root: Path | None = None,
    disable_cache: bool = True,
    clear_cache: bool = False,
) -> dict[str, str]:
    """Generate captions for image targets, using a file-backed cache.

    Cache key: "{model}::{sha1(image_bytes)}" stored in
    "<corpus_root>/media_captions.json". The corpus root is inferred from the
    target markdown path's parent directory (../ from markdown_dir).
    """
    # Partition targets that exist on disk
    existing = [t for t in targets if t.get("resolved") and t["resolved"].exists()]
    if not existing:
        return {}

    # Determine corpus root and cache path based on first target's markdown location if available.
    # We don't have direct access to target markdown path; instead, infer cache path
    # from the image location by assuming corpus structure (<root>/media/ ...).
    # Fallback to placing cache alongside the media directory or image file parent.
    def _guess_cache_path(sample: Path) -> Path:
        if cache_root is not None:
            return cache_root / "media_captions.json"
        # Fallback heuristic from media path
        parent = sample.parent
        root = parent.parent if parent.parent.exists() else parent
        return root / "media_captions.json"

    cache_path = _guess_cache_path(existing[0]["resolved"])  # type: ignore[index]
    model_key = (vision_model or os.environ.get("MSDR_GEMINI_VISION_MODEL", "gemini-2.5-flash-lite")).strip()

    if disable_cache:
        # No caching: caption everything available in a single API call, return mapping.
        from app.io import ensure_api_key  # Lazy import to avoid circular dependency
        try:
            ensure_api_key("gemini")
        except RuntimeError:
            LOGGER.warning('API key missing; skipping image caption generation')
            return {}
        requests = [ImageCaptionRequest(t["resolved"]) for t in existing]
        raw = caption_images(requests, model=vision_model)
        return {t["id"]: (raw.get(t["resolved"]) or "").strip() for t in existing if raw.get(t["resolved"]) }

    cache = _load_caption_cache(cache_path)
    if clear_cache and cache_path.exists():
        try:
            cache_path.unlink()
            cache = {}
        except OSError:
            LOGGER.warning("Failed to clear caption cache at %s", cache_path)
    captions: dict[str, str] = {}
    to_request: list[ImageCaptionRequest] = []
    request_lookup: dict[Path, tuple[str, str]] = {}

    for t in existing:
        path: Path = t["resolved"]  # type: ignore[assignment]
        try:
            blob = path.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha1(blob).hexdigest()
        key = f"{model_key}::{digest}"
        asset_id = t["id"]
        cached = cache.get(key)
        if isinstance(cached, str) and cached.strip():
            captions[asset_id] = cached.strip()
            continue
        req = ImageCaptionRequest(path)
        to_request.append(req)
        request_lookup[path] = (asset_id, key)

    if to_request:
        from app.io import ensure_api_key  # Lazy import to avoid circular dependency
        try:
            ensure_api_key("gemini")
        except RuntimeError:
            LOGGER.warning('API key missing; skipping image caption generation')
            to_request = []

    if to_request:
        raw = caption_images(to_request, model=vision_model)
        changed = False
        for p, text in raw.items():
            entry = request_lookup.get(p)
            if not entry:
                continue
            asset_id, key = entry
            if not text:
                continue
            cleaned = text.strip()
            if not cleaned:
                continue
            captions[asset_id] = cleaned
            if cache.get(key) != cleaned:
                cache[key] = cleaned
                changed = True
        if changed:
            _save_caption_cache(cache_path, cache)

    return captions


def _fallback_caption(bucket: dict) -> str:
    for alt in bucket.get("alts", []):
        if isinstance(alt, str) and alt.strip():
            return alt.strip()
    resolved = bucket.get("resolved")
    if isinstance(resolved, Path):
        return resolved.stem
    raw_path = bucket.get("raw_path")
    if isinstance(raw_path, str) and raw_path:
        name = Path(unquote(raw_path)).stem
        if name:
            return name
        return raw_path
    return "[이미지]"


def _load_caption_cache(path: Path) -> dict[str, str]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Ensure str->str mapping
                return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}
    except Exception:
        LOGGER.warning("Failed to read caption cache at %s; ignoring", path)
    return {}


def _save_caption_cache(path: Path, cache: dict[str, str]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        LOGGER.warning("Failed to write caption cache at %s", path)


__all__ = [
    "rewrite_markdown_with_captions",
    "CAPTION_START_MARKER",
    "CAPTION_END_MARKER",
]
