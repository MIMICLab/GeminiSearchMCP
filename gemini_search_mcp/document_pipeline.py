"""Document processing pipeline for Gemini document-based answers."""

from __future__ import annotations

import hashlib
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import CACHE_DIR
from .markdown_rewriter import rewrite_markdown_with_captions
from .pdf_converter import FileConverter

try:
    import opendataloader_pdf  # type: ignore
except ImportError:  # pragma: no cover - optional
    opendataloader_pdf = None  # type: ignore

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ProcessedDocument:
    """Represents a processed document ready for prompting."""

    source_path: Path
    pdf_path: Path
    markdown_path: Path
    rewritten_markdown_path: Path
    markdown_text: str


class DocumentPipeline:
    """Pipeline that prepares documents for Gemini question answering."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.converter = FileConverter(output_dir=self.cache_dir / "converted")

    def process(self, document_path: Path) -> ProcessedDocument:
        path = document_path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        signature = self._signature(path)
        doc_dir = self.cache_dir / signature
        doc_dir.mkdir(parents=True, exist_ok=True)

        rewritten = doc_dir / "document_rewritten.md"
        if rewritten.exists():
            text = rewritten.read_text(encoding="utf-8")
            existing_markdown = self._locate_existing_markdown(doc_dir)
            return ProcessedDocument(
                source_path=path,
                pdf_path=doc_dir / "document.pdf",
                markdown_path=existing_markdown or rewritten,
                rewritten_markdown_path=rewritten,
                markdown_text=text,
            )

        pdf_path = doc_dir / "document.pdf"

        self._ensure_pdf(path, pdf_path)
        markdown_path = self._pdf_to_markdown(pdf_path, doc_dir)

        rewritten_tmp = doc_dir / "rewritten_tmp.md"
        rewrite_markdown_with_captions(
            markdown_path,
            rewritten_tmp,
            source_hash=signature,
        )
        rewritten_tmp.replace(rewritten)
        text = rewritten.read_text(encoding="utf-8")
        return ProcessedDocument(
            source_path=path,
            pdf_path=pdf_path,
            markdown_path=markdown_path,
            rewritten_markdown_path=rewritten,
            markdown_text=text,
        )

    def _locate_existing_markdown(self, doc_dir: Path) -> Path | None:
        extracted_dir = doc_dir / "extracted"
        if not extracted_dir.exists():
            return None
        candidates = sorted(extracted_dir.glob("*.md"))
        return candidates[0] if candidates else None

    def _ensure_pdf(self, source: Path, target_pdf: Path) -> None:
        if source.suffix.lower() == ".pdf":
            target_pdf.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_pdf)
            return
        success, result = self.converter.convert_to_pdf(str(source), str(target_pdf))
        if not success:
            raise RuntimeError(f"Failed to convert {source} to PDF: {result}")

    def _pdf_to_markdown(self, pdf_path: Path, doc_dir: Path) -> Path:
        if opendataloader_pdf is None:
            raise RuntimeError(
                "opendataloader_pdf not installed; unable to extract markdown. Install the dependency and rerun."
            )

        tmp_output = doc_dir / "tmp_opendataloader"
        extracted_dir = doc_dir / "extracted"
        if tmp_output.exists():
            shutil.rmtree(tmp_output, ignore_errors=True)
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir, ignore_errors=True)
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

        shutil.move(str(tmp_output), str(extracted_dir))
        markdown_path = extracted_dir / md_candidates[0].name
        return markdown_path

    def _signature(self, path: Path) -> str:
        stats = path.stat()
        payload = f"{path}::{stats.st_size}::{stats.st_mtime}".encode("utf-8")
        return hashlib.sha1(payload).hexdigest()


__all__ = ["DocumentPipeline", "ProcessedDocument"]
