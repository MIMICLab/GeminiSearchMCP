"""Document conversion helpers with LibreOffice-first strategy."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

try:  # Optional dependency for markdown conversions
    import markdown  # type: ignore
except ImportError:  # pragma: no cover - optional
    markdown = None  # type: ignore

try:  # Optional dependency for converting images directly
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - optional
    Image = None  # type: ignore

LOGGER = logging.getLogger(__name__)

_CACHE_DIR = Path(tempfile.gettempdir()) / "msdr_converter_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class FileConverter:
    """Convert heterogeneous files to PDF using LibreOffice when possible."""

    OFFICE_FORMATS = {
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".odt", ".ods", ".odp", ".hwp", ".hwpx",
    }
    TEXT_FORMATS = {".txt", ".md", ".rtf", ".csv"}
    IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".jfif", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
    AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".wma", ".aac"}
    VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg"}

    SUPPORTED_FORMATS = {
        **{ext: "Office Document" for ext in OFFICE_FORMATS},
        **{ext: "Text Document" for ext in TEXT_FORMATS},
        **{ext: "Image" for ext in IMAGE_FORMATS},
        **{ext: "Audio" for ext in AUDIO_FORMATS},
        **{ext: "Video" for ext in VIDEO_FORMATS},
        ".pdf": "PDF",
    }

    def __init__(self, output_dir: Optional[Path] = None, timeout: int = 180) -> None:
        self.output_dir = output_dir or _CACHE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.libreoffice_cmd = self._detect_libreoffice()
        if self.libreoffice_cmd is None:
            LOGGER.warning("LibreOffice not detected; non-PDF conversions will fail")

    @classmethod
    def is_supported(cls, path: str | Path) -> bool:
        return Path(path).suffix.lower() in cls.SUPPORTED_FORMATS

    @classmethod
    def get_supported_formats(cls) -> dict[str, str]:
        return dict(cls.SUPPORTED_FORMATS)

    def convert_to_pdf(self, input_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """Convert ``input_path`` to PDF. Returns ``(success, path_or_error)``."""
        source = Path(input_path)
        if not source.exists():
            return False, f"File not found: {source}"

        ext = source.suffix.lower()
        if ext == ".pdf":
            return True, str(source)
        if not self.is_supported(source):
            return False, f"Unsupported format: {ext}"

        target = Path(output_path) if output_path else (self.output_dir / f"{source.stem}.pdf")
        target.parent.mkdir(parents=True, exist_ok=True)

        if ext in self.OFFICE_FORMATS:
            result = self._convert_via_libreoffice(source, target)
        elif ext in self.TEXT_FORMATS:
            result = self._convert_text(source, target)
        elif ext in self.IMAGE_FORMATS:
            result = self._convert_image(source, target)
        elif ext in self.AUDIO_FORMATS:
            result = self._convert_media_placeholder(source, target, media_type="audio")
        elif ext in self.VIDEO_FORMATS:
            result = self._convert_media_placeholder(source, target, media_type="video")
        else:
            result = (False, f"Unsupported extension: {ext}")

        return result

    # ------------------------------------------------------------------
    # Conversion handlers
    # ------------------------------------------------------------------
    def _convert_via_libreoffice(self, source: Path, target: Path) -> Tuple[bool, str]:
        if self.libreoffice_cmd is None:
            return False, "LibreOffice not available"

        temp_dir = Path(tempfile.mkdtemp(prefix="libreoffice_", dir=str(self.output_dir)))
        try:
            cmd = [
                self.libreoffice_cmd,
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_dir),
                str(source),
            ]
            LOGGER.debug("Running LibreOffice: %s", " ".join(cmd))
            proc = subprocess.run(  # noqa: PLW1510 (capture output for diagnostics)
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if proc.returncode != 0:
                error = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
                LOGGER.error("LibreOffice failed (%s): %s", source.name, error)
                return False, error

            produced = temp_dir / f"{source.stem}.pdf"
            if not produced.exists():
                # LibreOffice sometimes appends suffixes
                candidates = list(temp_dir.glob("*.pdf"))
                if candidates:
                    produced = candidates[0]
            if not produced.exists():
                return False, "LibreOffice did not produce output"

            shutil.move(str(produced), str(target))
            return True, str(target)
        except subprocess.TimeoutExpired:
            return False, "LibreOffice conversion timed out"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _convert_text(self, source: Path, target: Path) -> Tuple[bool, str]:
        if source.suffix.lower() == ".md":
            rendered = (
                markdown.markdown(source.read_text(encoding="utf-8"))
                if markdown is not None
                else source.read_text(encoding="utf-8")
            )
            suffix = ".html" if markdown is not None else ".txt"
            fd, tmp_name = tempfile.mkstemp(prefix="md_", suffix=suffix, dir=str(self.output_dir))
            os.close(fd)
            temp_path = Path(tmp_name)
            temp_path.write_text(rendered, encoding="utf-8")
            try:
                return self._convert_via_libreoffice(temp_path, target)
            finally:
                temp_path.unlink(missing_ok=True)

        # Default: let LibreOffice handle raw text/CSV/RTF
        return self._convert_via_libreoffice(source, target)

    def _convert_image(self, source: Path, target: Path) -> Tuple[bool, str]:
        if Image is None:
            return False, "Pillow not installed – cannot convert images"
        try:
            with Image.open(source) as img:
                rgb = img.convert("RGB")
                rgb.save(target, format="PDF")
            return True, str(target)
        except Exception as exc:  # pragma: no cover - Pillow runtime errors
            LOGGER.error("Image conversion failed: %s", exc)
            return False, str(exc)

    def _convert_media_placeholder(self, source: Path, target: Path, *, media_type: str) -> Tuple[bool, str]:
        if self.libreoffice_cmd is None:
            return False, f"LibreOffice required to render {media_type} summary"

        info = self._collect_media_info(source)
        text_lines = [
            f"Media type: {media_type}",
            f"Original file: {source.name}",
            f"Size (bytes): {info.get('size_bytes', 'unknown')}",
        ]
        for key in ("duration", "codec", "bitrate"):
            if key in info:
                text_lines.append(f"{key.capitalize()}: {info[key]}")
        payload = "\n".join(text_lines)

        fd, tmp_name = tempfile.mkstemp(prefix="media_", suffix=".txt", dir=str(self.output_dir))
        os.close(fd)
        temp_txt = Path(tmp_name)
        temp_txt.write_text(payload, encoding="utf-8")
        result = self._convert_via_libreoffice(temp_txt, target)
        temp_txt.unlink(missing_ok=True)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_media_info(self, source: Path) -> dict[str, str | int]:
        info: dict[str, str | int] = {"size_bytes": source.stat().st_size}
        probe_path = shutil.which("ffprobe")
        if not probe_path:
            return info
        try:
            cmd = [
                probe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration,bit_rate",
                "-of",
                "json",
                str(source),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                fmt = data.get("format", {})
                if "duration" in fmt:
                    info["duration"] = fmt["duration"]
                if "bit_rate" in fmt:
                    info["bitrate"] = fmt["bit_rate"]
        except Exception as exc:  # pragma: no cover - best-effort metadata
            LOGGER.debug("ffprobe metadata failed: %s", exc)
        return info

    def _detect_libreoffice(self) -> str | None:
        candidates = ["libreoffice", "soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]
        for candidate in candidates:
            path = shutil.which(candidate) if not candidate.startswith("/") else (candidate if Path(candidate).exists() else None)
            if path:
                return path
        return None
