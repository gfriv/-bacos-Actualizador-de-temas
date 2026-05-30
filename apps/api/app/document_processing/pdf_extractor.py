from pathlib import Path

from pypdf import PdfReader

SCANNED_PDF_MESSAGE = "Este PDF parece escaneado. Será necesario OCR en una fase posterior."


def extract_pdf_text(path: str | Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    extracted = "\n\n".join(pages).strip()
    if not extracted:
        raise ValueError(SCANNED_PDF_MESSAGE)
    return extracted
