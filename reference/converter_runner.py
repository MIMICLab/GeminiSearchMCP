"""Run file conversion and markdown extraction pipeline."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from .pdf_converter import FileConverter
from app.utils.hash import relpath_hash

try:  # pragma: no cover - optional dependency
    import opendataloader_pdf  # type: ignore
except ImportError:  # pragma: no cover
    opendataloader_pdf = None  # type: ignore

from .chunker import chunk_markdown
from .markdown_rewriter import rewrite_markdown_with_captions

LOGGER = logging.getLogger(__name__)

DEFAULT_CONVERSION_ATTEMPTS = 3
RETRY_ELIGIBLE_EXTENSIONS = {
    ".hwp",
    ".hwpx",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
}

@dataclass
class ChunkRecord:
    """Minimal representation of a corpus chunk."""

    chunk_id: str
    source_path: Path
    markdown_path: Path
    metadata: dict = field(default_factory=dict)


@dataclass
class CorpusManifest:
    """Collection of chunks and bookkeeping info for downstream steps."""

    chunks: list[ChunkRecord]
    output_dir: Path
    uploads_dir: Path
    needs_embedding_refresh: bool = True

    def chunk_ids(self) -> Iterator[str]:
        for chunk in self.chunks:
            yield chunk.chunk_id


@dataclass
class ConversionConfig:
    input_dir: Path
    output_dir: Path
    extra_options: dict = field(default_factory=dict)
    enable_chunking: bool = True
    vision_model: str | None = None
    disable_caption_cache: bool = False
    clear_caption_cache: bool = False

    @property
    def converted_dir(self) -> Path:
        path = self.output_dir / "converted"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def markdown_dir(self) -> Path:
        path = self.output_dir / "markdown"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def originals_dir(self) -> Path:
        path = self.output_dir / "originals"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def media_dir(self) -> Path:
        path = self.output_dir / "media"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chunks_dir(self) -> Path:
        path = self.output_dir / "chunk_markdown"
        path.mkdir(parents=True, exist_ok=True)
        return path


@dataclass
class PreparedSource:
    source_path: Path
    markdown_path: Path
    media_assets: list[dict]
    source_rel: Path
    source_hash: str


def run_conversion_pipeline(config: ConversionConfig) -> CorpusManifest:
    """Convert uploads, extract markdown, and build manifest."""

    uploads = _deduplicate_paths(list(_iter_source_files(config.input_dir)))
    try:
        # Emit discovery event for UI progress (optional consumer)
        print(json.dumps({
            "stage": "preprocess",
            "sub": "discover",
            "total": len(uploads),
            "input_dir": str(config.input_dir),
        }, ensure_ascii=False), flush=True)
    except Exception:
        pass
    if not uploads:
        LOGGER.info("No input files found in %s", config.input_dir)
        return CorpusManifest(
            chunks=[],
            output_dir=config.output_dir,
            uploads_dir=config.input_dir,
            needs_embedding_refresh=False,
        )

    existing_chunk_map = _load_existing_chunk_map(config) if config.enable_chunking else {}
    chunks: list[ChunkRecord] = []
    errors: list[str] = []
    seen_chunk_ids: set[str] = set()

    prepared_items: list[PreparedSource] = []
    prepared_lookup: list[tuple[str, PreparedSource]] = []

    total = len(uploads)
    current = 0
    for src in uploads:
        current += 1
        try:
            print(json.dumps({
                "stage": "preprocess",
                "sub": "convert_start",
                "current": current,
                "total": total,
                "file": str(src),
            }, ensure_ascii=False), flush=True)
        except Exception:
            pass
        source_rel = _compute_source_rel(src, config.input_dir)
        source_hash = relpath_hash(config.input_dir, source_rel)
        copied = _copy_original(src, config.originals_dir, source_hash)
        key = source_hash
        existing_chunks = existing_chunk_map.get(key, []) if config.enable_chunking else []
        if existing_chunks and not _chunks_match_hash(existing_chunks, source_hash):
            _remove_chunk_artifacts(existing_chunks, config.output_dir)
            existing_chunks = []
        pdf_path = config.converted_dir / f"{source_hash}.pdf"
        markdown_path = config.markdown_dir / f"{source_hash}.md"

        if config.enable_chunking:
            if _should_skip_reprocessing(copied, pdf_path, markdown_path, existing_chunks):
                for chunk in existing_chunks:
                    if chunk.markdown_path.exists() and chunk.chunk_id not in seen_chunk_ids:
                        chunks.append(chunk)
                        seen_chunk_ids.add(chunk.chunk_id)
                existing_chunk_map[key] = []
                continue
        else:
            if _artifacts_up_to_date(copied, pdf_path, markdown_path):
                continue

        try:
            prepared = _prepare_source_file(
                config,
                src,
                copied=copied,
                source_rel=source_rel,
                source_hash=source_hash,
            )
            try:
                print(json.dumps({
                    "stage": "preprocess",
                    "sub": "extract_done",
                    "current": current,
                    "total": total,
                    "file": str(src),
                }, ensure_ascii=False), flush=True)
            except Exception:
                pass
            if config.enable_chunking:
                prepared_items.append(prepared)
                prepared_lookup.append((key, prepared))
        except Exception as exc:  # noqa: BLE001
            message = f"Failed to process {src}: {exc}"
            LOGGER.error(message)
            errors.append(message)

    if errors:
        raise RuntimeError("\n".join(errors))

    if config.enable_chunking and prepared_items:
        max_workers = min(max(1, os.cpu_count() or 1), len(prepared_items))
        LOGGER.info(
            "Chunking %d prepared documents using %d workers",
            len(prepared_items),
            max_workers,
        )
        try:
            print(json.dumps({
                "stage": "preprocess",
                "sub": "chunk_start",
                "total": len(prepared_items),
            }, ensure_ascii=False), flush=True)
        except Exception:
            pass

        if len(prepared_items) == 1 or max_workers == 1:
            done = 0
            for key, prepared in prepared_lookup:
                try:
                    chunk_records = _chunk_prepared_source(config, prepared)
                    chunks.extend(chunk_records)
                    seen_chunk_ids.update(record.chunk_id for record in chunk_records)
                    existing_chunk_map[key] = []
                    done += 1
                    try:
                        print(json.dumps({
                            "stage": "preprocess",
                            "sub": "chunk_progress",
                            "current": done,
                            "total": len(prepared_items),
                        }, ensure_ascii=False), flush=True)
                    except Exception:
                        pass
                except Exception as exc:  # noqa: BLE001
                    message = f"Failed to chunk {prepared.markdown_path}: {exc}"
                    LOGGER.error(message)
                    errors.append(message)
        else:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(_chunk_prepared_source, config, prepared): (key, prepared)
                    for key, prepared in prepared_lookup
                }
                done = 0
                for future in as_completed(future_map):
                    key, prepared = future_map[future]
                    try:
                        chunk_records = future.result()
                        chunks.extend(chunk_records)
                        seen_chunk_ids.update(record.chunk_id for record in chunk_records)
                        existing_chunk_map[key] = []
                        done += 1
                        try:
                            print(json.dumps({
                                "stage": "preprocess",
                                "sub": "chunk_progress",
                                "current": done,
                                "total": len(prepared_items),
                            }, ensure_ascii=False), flush=True)
                        except Exception:
                            pass
                    except Exception as exc:  # noqa: BLE001
                        message = f"Failed to chunk {prepared.markdown_path}: {exc}"
                        LOGGER.error(message)
                        errors.append(message)

    if errors:
        raise RuntimeError("\n".join(errors))

    if config.enable_chunking:
        # Include untouched existing chunks (e.g., sources not present in this run)
        for chunk_list in existing_chunk_map.values():
            for chunk in chunk_list:
                if chunk.chunk_id in seen_chunk_ids:
                    continue
                if chunk.markdown_path.exists():
                    chunks.append(chunk)
                    seen_chunk_ids.add(chunk.chunk_id)

    manifest = CorpusManifest(
        chunks=chunks,
        output_dir=config.output_dir,
        uploads_dir=config.input_dir,
        needs_embedding_refresh=config.enable_chunking,
    )
    return manifest


def _process_source_file(config: ConversionConfig, src: Path) -> list[ChunkRecord]:
    prepared = _prepare_source_file(config, src)
    return _chunk_prepared_source(config, prepared)


def _prepare_source_file(
    config: ConversionConfig,
    src: Path,
    *,
    copied: Path | None = None,
    source_rel: Path | None = None,
    source_hash: str | None = None,
) -> PreparedSource:
    rel_path = source_rel or _compute_source_rel(src, config.input_dir)
    hash_id = source_hash or _compute_source_hash(rel_path, config.input_dir)
    copied = copied or _copy_original(src, config.originals_dir, hash_id)
    converter = FileConverter(output_dir=config.converted_dir)
    pdf_path = _convert_to_pdf(
        copied,
        config.converted_dir,
        converter,
        config.extra_options,
        hash_id,
    )
    markdown_master, media_assets = _render_markdown_and_assets(
        pdf_path,
        config,
        hash_id,
    )
    return PreparedSource(
        source_path=copied,
        markdown_path=markdown_master,
        media_assets=media_assets,
        source_rel=rel_path,
        source_hash=hash_id,
    )


def _chunk_prepared_source(
    config: ConversionConfig, prepared: PreparedSource
) -> list[ChunkRecord]:
    chunk_records: list[ChunkRecord] = []
    chunk_prefix = prepared.source_hash
    source_rel_str = prepared.source_rel.as_posix()
    for chunk_suffix, chunk_text, metadata in chunk_markdown(
        prepared.markdown_path,
        source_path=prepared.source_path,
        media_assets=prepared.media_assets,
        chunk_prefix=chunk_prefix,
    ):
        metadata.setdefault("source_rel", source_rel_str)
        metadata.setdefault("source_hash", prepared.source_hash)
        chunk_id = f"chnk_{chunk_suffix}"
        chunk_path = config.chunks_dir / f"{chunk_id}.md"
        chunk_path.write_text(chunk_text, encoding="utf-8")
        chunk_records.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_path=prepared.source_path,
                markdown_path=chunk_path,
                metadata=metadata,
            )
        )
    if not chunk_records:
        raise RuntimeError(
            f"Chunking produced no output for {prepared.markdown_path}"
        )
    return chunk_records

def _should_skip_reprocessing(
    copied: Path,
    pdf_path: Path,
    markdown_path: Path,
    existing_chunks: list[ChunkRecord],
) -> bool:
    if not existing_chunks:
        return False

    try:
        source_mtime = copied.stat().st_mtime
    except FileNotFoundError:
        return False

    if not pdf_path.exists() or pdf_path.stat().st_mtime < source_mtime:
        return False

    if not markdown_path.exists() or markdown_path.stat().st_mtime < pdf_path.stat().st_mtime:
        return False

    for chunk in existing_chunks:
        if not chunk.markdown_path.exists():
            return False
        if chunk.markdown_path.stat().st_mtime < markdown_path.stat().st_mtime:
            return False

    return True


def _artifacts_up_to_date(source: Path, pdf_path: Path, markdown_path: Path) -> bool:
    try:
        source_mtime = source.stat().st_mtime
    except FileNotFoundError:
        return False

    try:
        pdf_mtime = pdf_path.stat().st_mtime
    except FileNotFoundError:
        return False
    if pdf_mtime < source_mtime:
        return False

    try:
        markdown_mtime = markdown_path.stat().st_mtime
    except FileNotFoundError:
        return False
    return markdown_mtime >= pdf_mtime


def _chunks_match_hash(existing_chunks: list[ChunkRecord], source_hash: str) -> bool:
    prefix = f"chnk_{source_hash}_"
    return all(chunk.chunk_id.startswith(prefix) for chunk in existing_chunks)


def _remove_chunk_artifacts(chunks: Iterable[ChunkRecord], output_dir: Path) -> None:
    texts_dir = output_dir / "CHUNKS_TEXTS"
    for chunk in chunks:
        try:
            chunk.markdown_path.unlink(missing_ok=True)
        except OSError:
            LOGGER.debug("Failed to remove stale chunk markdown %s", chunk.markdown_path)
        try:
            (texts_dir / f"{chunk.chunk_id}.md").unlink(missing_ok=True)
        except OSError:
            LOGGER.debug("Failed to remove stale chunk text %s", chunk.chunk_id)


def _load_existing_chunk_map(config: ConversionConfig) -> dict[str, list[ChunkRecord]]:
    from app.utils.jsonl import read_jsonl

    jsonl_path = config.output_dir / "CHUNKS.jsonl"
    if not jsonl_path.exists():
        return {}

    chunk_map: dict[str, list[ChunkRecord]] = {}
    try:
        records = read_jsonl(jsonl_path)
    except Exception:
        records = []

    for record in records:
        if not isinstance(record, dict):
            continue
        chunk_id = record.get("id")
        source_path = record.get("source_path")
        source_rel_raw = record.get("source_rel")
        source_rel = Path(source_rel_raw) if source_rel_raw else None
        source_hash = record.get("source_hash")
        if not source_hash and source_rel is not None:
            source_hash = relpath_hash(config.input_dir, source_rel)
        if not chunk_id or not source_path or not source_hash:
            continue

        source = Path(source_path)
        chunk_path = config.chunks_dir / f"{chunk_id}.md"
        if not chunk_path.exists():
            alt_path = config.output_dir / "CHUNKS_TEXTS" / f"{chunk_id}.md"
            if alt_path.exists():
                chunk_path = alt_path
            else:
                continue

        source_rel = source_rel or Path(source.name)
        metadata = {
            "media_assets": record.get("media_assets", []),
            "source_rel": source_rel.as_posix(),
            "source_hash": source_hash,
        }
        chunk_record = ChunkRecord(
            chunk_id=str(chunk_id),
            source_path=source,
            markdown_path=chunk_path,
            metadata=metadata,
        )
        key = source_hash
        chunk_map.setdefault(key, []).append(chunk_record)
    return chunk_map


def _iter_source_files(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file():
            continue

        try:
            relative_parts = path.relative_to(input_dir).parts
        except ValueError:
            relative_parts = path.parts

        if any(part.startswith(".") for part in relative_parts):
            LOGGER.debug("Skipping hidden file %s", path)
            continue

        if path.suffix.lower() not in RETRY_ELIGIBLE_EXTENSIONS and path.suffix.lower() != ".pdf":
            LOGGER.debug("Skipping unsupported file %s", path)
            continue

        yield path


def _deduplicate_paths(paths: list[Path]) -> list[Path]:
    if not paths:
        return []
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        key = path.resolve()
        if key in seen:
            LOGGER.debug("Skipping duplicate file %s", path)
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _compute_source_rel(source: Path, input_root: Path) -> Path:
    try:
        relative = source.relative_to(input_root)
    except ValueError:
        relative = Path(source.name)
    return Path(relative)


 # source hash calculation centralized in app.utils.hash


def _copy_original(
    source: Path,
    originals_dir: Path,
    source_hash: str,
) -> Path:
    ext = source.suffix.lower()
    target = originals_dir / f"{source_hash}{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or source.stat().st_mtime > target.stat().st_mtime:
        LOGGER.debug("Copying %s -> %s", source, target)
        shutil.copy2(source, target)
    return target

def _convert_to_pdf(
    source: Path,
    converted_dir: Path,
    converter: FileConverter | None,
    options: dict,
    source_hash: str,
) -> Path:
    ext = source.suffix.lower()
    pdf_path = converted_dir / f"{source_hash}.pdf"

    if ext == ".pdf":
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        if not pdf_path.exists() or source.stat().st_mtime > pdf_path.stat().st_mtime:
            shutil.copy2(source, pdf_path)
        return pdf_path

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        return pdf_path

    if converter is None:
        raise RuntimeError("FileConverter not available to convert non-PDF source")

    attempts = options.get("max_conversion_attempts")
    try:
        attempts = int(attempts) if attempts is not None else DEFAULT_CONVERSION_ATTEMPTS
    except (TypeError, ValueError):
        LOGGER.warning("Ignoring invalid max_conversion_attempts=%r; falling back to %d attempts", attempts, DEFAULT_CONVERSION_ATTEMPTS)
        attempts = DEFAULT_CONVERSION_ATTEMPTS
    attempts = max(1, attempts)

    if ext not in RETRY_ELIGIBLE_EXTENSIONS and attempts > 1:
        LOGGER.debug(
            "Skipping retries for extension %s; proceeding with a single attempt",
            ext or "<none>",
        )
        attempts = 1

    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        if attempt == 1:
            LOGGER.info("Converting %s to PDF", source)
        else:
            LOGGER.info("Retrying conversion (%d/%d) for %s", attempt, attempts, source)
        success, result = converter.convert_to_pdf(str(source), str(pdf_path))
        if success:
            produced = Path(result)
            if produced != pdf_path:
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(produced, pdf_path)
            return pdf_path

        last_error = str(result)
        LOGGER.warning("Conversion attempt %d/%d for %s failed: %s", attempt, attempts, source, last_error)
        if pdf_path.exists():
            pdf_path.unlink(missing_ok=True)

    attempt_word = "attempt" if attempts == 1 else "attempts"
    raise RuntimeError(
        f"Failed to convert {source} to PDF after {attempts} {attempt_word}: {last_error or 'unknown error'}"
    )


def _render_markdown_and_assets(
    pdf_path: Path,
    config: ConversionConfig,
    source_hash: str,
) -> tuple[Path, list[dict]]:
    target_path = config.markdown_dir / f"{source_hash}.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if opendataloader_pdf is None:
        raise RuntimeError(
            "opendataloader_pdf not installed; unable to extract markdown. Install the dependency and rerun."
        )

    tmp_output = target_path.parent / f"{target_path.stem}_opendata"
    if tmp_output.exists():
        shutil.rmtree(tmp_output, ignore_errors=True)
    tmp_output.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Extracting markdown from %s", pdf_path)
    opendataloader_pdf.run(
        input_path=str(pdf_path),
        output_folder=str(tmp_output),
        generate_markdown=True,
        add_image_to_markdown=True,
    )
    md_candidates = sorted(tmp_output.glob("*.md"))
    if not md_candidates:
        raise RuntimeError(f"Markdown extraction produced no files for {pdf_path}")

    media_assets = rewrite_markdown_with_captions(
        md_candidates[0],
        target_path,
        source_hash,
        vision_model=config.vision_model,
        disable_cache=config.disable_caption_cache,
        clear_cache=config.clear_caption_cache,
    )
    return target_path, media_assets
