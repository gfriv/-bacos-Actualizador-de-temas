import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
WHITESPACE_RE = re.compile(r"[ \t]+")


class OCRUnavailableError(RuntimeError):
    pass


class OCRProcessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class OCRConfig:
    languages: str = "spa+eng"
    dpi: int = 200
    max_pages: int = 40
    timeout_seconds: int = 30
    tesseract_cmd: str = ""


def extract_pdf_ocr_text(path: str | Path, config: OCRConfig) -> str:
    pdfium = _load_pdfium()
    pytesseract = _load_pytesseract()
    tesseract_not_found_error = pytesseract.TesseractNotFoundError
    tesseract_error = pytesseract.TesseractError

    _configure_tesseract(pytesseract, config.tesseract_cmd)
    _assert_tesseract_available(pytesseract, tesseract_not_found_error)

    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise OCRProcessingError("No se pudo preparar el PDF para OCR.") from exc

    parts: list[str] = []
    page_count = len(pdf)
    page_limit = max(0, min(page_count, config.max_pages))
    scale = max(config.dpi, 72) / 72

    try:
        for page_index in range(page_limit):
            page = pdf[page_index]
            bitmap = None
            image = None
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                text = pytesseract.image_to_string(
                    image,
                    lang=config.languages,
                    config="--psm 6",
                    timeout=config.timeout_seconds,
                )
            except RuntimeError as exc:
                raise OCRProcessingError(
                    "El OCR ha superado el tiempo maximo por pagina. Reduce el PDF o aumenta OCR_TIMEOUT_SECONDS."
                ) from exc
            except tesseract_not_found_error as exc:
                raise _missing_tesseract_error() from exc
            except tesseract_error as exc:
                raise OCRProcessingError(
                    f"No se pudo completar OCR. Revisa que Tesseract tenga instalados los idiomas: {config.languages}."
                ) from exc
            finally:
                if image is not None and hasattr(image, "close"):
                    image.close()
                if bitmap is not None and hasattr(bitmap, "close"):
                    bitmap.close()
                if hasattr(page, "close"):
                    page.close()

            clean_text = _clean_ocr_text(text)
            if clean_text:
                parts.append(f"[Pagina {page_index + 1} - OCR]\n{clean_text}")
    finally:
        if hasattr(pdf, "close"):
            pdf.close()

    if page_count > page_limit and parts:
        parts.append(
            f"[OCR limitado] Se procesaron {page_limit} de {page_count} paginas. "
            "Ajusta OCR_MAX_PAGES si necesitas procesar el documento completo."
        )

    return "\n\n".join(parts).strip()


def _load_pdfium() -> Any:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise OCRUnavailableError(
            "El renderizador PDF para OCR no esta instalado. Instala la dependencia opcional pypdfium2."
        ) from exc
    return pdfium


def _load_pytesseract() -> Any:
    try:
        import pytesseract
    except ImportError as exc:
        raise OCRUnavailableError(
            "El adaptador OCR no esta instalado. Instala la dependencia opcional pytesseract."
        ) from exc
    return pytesseract


def _configure_tesseract(pytesseract: Any, tesseract_cmd: str) -> None:
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def _assert_tesseract_available(
    pytesseract: Any, tesseract_not_found_error: type[Exception]
) -> None:
    try:
        pytesseract.get_tesseract_version()
    except tesseract_not_found_error as exc:
        raise _missing_tesseract_error() from exc


def _missing_tesseract_error() -> OCRUnavailableError:
    return OCRUnavailableError(
        "Tesseract OCR no esta disponible en el servidor. Instalalo o configura OCR_TESSERACT_CMD."
    )


def _clean_ocr_text(value: str) -> str:
    without_controls = CONTROL_CHARS_RE.sub(" ", value)
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in without_controls.splitlines()]
    return "\n".join(line for line in lines if line).strip()
