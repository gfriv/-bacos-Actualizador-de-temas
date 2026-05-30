from pathlib import Path

from docx import Document as DocxDocument


def extract_docx_text(path: str | Path) -> str:
    document = DocxDocument(str(path))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)
