import zipfile
from io import BytesIO


def validate_document_bytes(content: bytes, suffix: str) -> None:
    if suffix == ".pdf":
        if not content.lstrip().startswith(b"%PDF-"):
            raise ValueError("El archivo no parece un PDF válido.")
        return

    if suffix == ".docx":
        buffer = BytesIO(content)
        if not zipfile.is_zipfile(buffer):
            raise ValueError("El archivo no parece un DOCX válido.")
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as archive:
            if "[Content_Types].xml" not in archive.namelist() or "word/document.xml" not in archive.namelist():
                raise ValueError("El archivo no parece un DOCX válido.")
        return

    raise ValueError("Solo se aceptan archivos DOCX o PDF.")
