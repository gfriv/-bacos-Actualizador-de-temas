import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.core.config import settings
from app.document_processing.ocr_extractor import (
    OCRConfig,
    OCRProcessingError,
    OCRUnavailableError,
    extract_pdf_ocr_text,
)

SCANNED_PDF_MESSAGE = "Este PDF parece escaneado. Será necesario OCR en una fase posterior."
OCR_NO_TEXT_MESSAGE = (
    "Este PDF parece escaneado. El OCR se ha ejecutado, pero no ha recuperado texto suficiente."
)
TEXT_THRESHOLD_CHARS = 20
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
WHITESPACE_RE = re.compile(r"[ \t]+")


def extract_pdf_text(path: str | Path, *, ocr_enabled: bool | None = None) -> str:
    """Extract PDF text, falling back to OCR for scanned PDFs when enabled."""

    extracted = _extract_with_pdfplumber(path)
    if _has_meaningful_text(extracted):
        return extracted

    extracted = _extract_with_pypdf(path)
    if _has_meaningful_text(extracted):
        return extracted

    should_run_ocr = settings.ocr_enabled if ocr_enabled is None else ocr_enabled
    if should_run_ocr:
        ocr_text = _extract_with_ocr(path)
        if _has_meaningful_text(ocr_text):
            return ocr_text
        raise ValueError(OCR_NO_TEXT_MESSAGE)

    raise ValueError(SCANNED_PDF_MESSAGE)


def _extract_with_ocr(path: str | Path) -> str:
    config = OCRConfig(
        languages=settings.ocr_languages,
        dpi=settings.ocr_dpi,
        max_pages=settings.ocr_max_pages,
        timeout_seconds=settings.ocr_timeout_seconds,
        tesseract_cmd=settings.ocr_tesseract_cmd,
    )
    try:
        return extract_pdf_ocr_text(path, config)
    except OCRUnavailableError as exc:
        raise ValueError(f"{SCANNED_PDF_MESSAGE} {exc}") from exc
    except OCRProcessingError as exc:
        raise ValueError(str(exc)) from exc


def _extract_with_pdfplumber(path: str | Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        return ""

    parts: list[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                page_parts: list[str] = []
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                if text.strip():
                    page_parts.append(_clean_pdf_text(text))
                for table in page.extract_tables() or []:
                    rendered = _render_pdf_table(table)
                    if rendered:
                        page_parts.append(rendered)
                if page_parts:
                    parts.append(f"[Página {index}]\n" + "\n\n".join(page_parts))
    except Exception:
        return ""
    return "\n\n".join(parts).strip()


def _extract_with_pypdf(path: str | Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_pdf_text(page.extract_text() or "")
        if text:
            pages.append(f"[Página {index}]\n{text}")
    return "\n\n".join(pages).strip()


def _render_pdf_table(table: list[list[Any]]) -> str:
    rows = [
        [_clean_pdf_text("" if cell is None else str(cell)) for cell in row]
        for row in table
        if row and any(cell is not None and str(cell).strip() for cell in row)
    ]
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = normalized_rows[0]
    separator = ["---"] * width
    body = normalized_rows[1:]
    lines = [
        "| " + " | ".join(_escape_table_cell(cell) for cell in header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(_escape_table_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def _clean_pdf_text(value: str) -> str:
    without_controls = CONTROL_CHARS_RE.sub(" ", value)
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in without_controls.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _has_meaningful_text(text: str) -> bool:
    compact = " ".join(text.split())
    if len(compact) >= TEXT_THRESHOLD_CHARS:
        return True
    return len(compact.split()) >= 3
