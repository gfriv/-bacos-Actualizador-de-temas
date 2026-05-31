from __future__ import annotations

import re
from typing import Any

from app.llm.schemas import ModelConfig


class MockProvider:
    name = "mock"

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        return (
            "## Resultado simulado\n\n"
            "Este contenido ha sido generado por MockProvider para desarrollo sin costes. "
            "Requiere revisi\u00f3n docente antes de cualquier consolidaci\u00f3n."
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        data = {
            "section_title": "Introducci\u00f3n",
            "original_fragment": "Referencia o formulaci\u00f3n que debe revisarse.",
            "issue_detected": "Posible desactualizaci\u00f3n o falta de contexto normativo.",
            "proposed_change": "Actualizar de forma localizada y marcar para revisi\u00f3n docente.",
            "justification": "Propuesta simulada para validar el flujo del MVP.",
            "source_reference": "MockProvider; requiere fuente real antes de aprobaci\u00f3n.",
            "confidence_level": "medium",
            "needs_human_verification": True,
        }
        return schema.model_validate(data) if schema else data

    async def summarize(self, text: str, instructions: str | None = None) -> str:
        return f"Resumen simulado: {text[:220]}"

    async def extract_structured_data(self, text: str, schema: type[Any]) -> Any:
        return await self.generate_json(text, schema=schema)

    async def generate_document_resource(self, document: str, resource_type: str) -> str:
        title = _document_title(document)
        sections = _document_sections(document)
        key_terms = _key_terms(document)
        body = _resource_body(resource_type, title, sections, key_terms)
        return (
            f"# {resource_type.replace('_', ' ').title()}\n\n"
            "Recurso did\u00e1ctico simulado generado desde el documento consolidado.\n\n"
            f"{body}\n\n"
            "## Control docente\n\n"
            "- Mantiene alineaci\u00f3n conceptual con el documento consolidado.\n"
            "- No a\u00f1ade contenido cient\u00edfico nuevo.\n"
            "- Requiere revisi\u00f3n docente antes de uso final."
        )


HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
WORD_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]{4,}\b")


def _document_title(document: str) -> str:
    headings = list(HEADING_PATTERN.finditer(document or ""))
    if headings:
        return headings[0].group(2).strip()
    return "Documento consolidado"


def _document_sections(document: str) -> list[str]:
    headings = [match.group(2).strip() for match in HEADING_PATTERN.finditer(document or "")]
    sections = [heading for heading in headings[1:] if heading]
    return sections[:8] or [_document_title(document)]


def _key_terms(document: str) -> list[str]:
    stop = {
        "desde",
        "sobre",
        "entre",
        "documento",
        "consolidado",
        "revision",
        "docente",
        "asistencia",
        "abacos",
        "centro",
        "formacion",
        "estudios",
    }
    normalized = _normalize(document)
    return [word for word in dict.fromkeys(WORD_PATTERN.findall(normalized)) if word not in stop][:10]


def _resource_body(resource_type: str, title: str, sections: list[str], key_terms: list[str]) -> str:
    readable_terms = ", ".join(key_terms[:6]) or "conceptos principales del documento"
    if resource_type == "esquema_desarrollado":
        lines = ["## Esquema desarrollado", f"**Tema base:** {title}", ""]
        for index, section in enumerate(sections[:6], start=1):
            lines.append(f"{index}. **{section}**")
            lines.append("   - Idea central recuperada del consolidado.")
            lines.append("   - Relacion con el conjunto del tema y revision docente pendiente.")
        lines.append("")
        lines.append(f"Conceptos de apoyo: {readable_terms}.")
        return "\n".join(lines)
    if resource_type == "test_autoevaluacion":
        return "\n\n".join(
            [
                "## Test de autoevaluacion",
                _question_block(1, f"Que apartado estructura el nucleo del tema {title}?", sections[0]),
                _question_block(2, "Que debe comprobar el docente antes de usar el recurso?", "La validez del consolidado"),
                _question_block(3, "Que conceptos conviene repasar?", readable_terms),
            ]
        )
    if resource_type == "presentacion_clase":
        slides = ["## Presentacion estructurada"]
        for index, section in enumerate(sections[:7], start=1):
            slides.append(f"- **Diapositiva {index}: {section}**")
            slides.append("  - Mensaje principal: sintesis fiel al consolidado.")
            slides.append("  - Apoyo oral: relacionar con el hilo argumental del tema.")
        slides.append("- **Cierre:** ideas clave y comprobacion docente.")
        return "\n".join(slides)
    if resource_type == "guion_audio":
        return (
            "## Guion de audio\n\n"
            f"**Entrada:** Presentacion breve del tema {title}.\n\n"
            f"**Desarrollo:** Recorrido ordenado por {', '.join(sections[:4])}.\n\n"
            f"**Repaso:** Terminos a fijar: {readable_terms}.\n\n"
            "**Cierre:** Recordatorio de que el material deriva del consolidado validado."
        )
    if resource_type == "guion_video":
        return (
            "## Guion de video resumen\n\n"
            f"1. **Apertura:** titulo en pantalla, {title}.\n"
            f"2. **Mapa visual:** mostrar secciones: {', '.join(sections[:5])}.\n"
            "3. **Desarrollo:** explicar cada bloque con ejemplos presentes en el consolidado.\n"
            f"4. **Cierre:** conceptos clave: {readable_terms}.\n"
            "5. **Nota final:** revision docente obligatoria antes de difusion."
        )
    return (
        "## Recurso derivado\n\n"
        f"- Tema base: {title}.\n"
        f"- Secciones de referencia: {', '.join(sections[:6])}.\n"
        f"- Conceptos clave: {readable_terms}."
    )


def _question_block(number: int, question: str, answer: str) -> str:
    return (
        f"### Pregunta {number}\n"
        f"{question}\n\n"
        "- A. Una idea no presente en el documento.\n"
        "- B. Un elemento recuperado del documento consolidado.\n"
        "- C. Una referencia sin verificar.\n\n"
        f"**Respuesta correcta:** B. {answer}.\n"
        "**Explicacion:** La respuesta debe proceder del documento consolidado y revisado."
    )


def _normalize(text: str) -> str:
    replacements = str.maketrans(
        "\u00e1\u00e9\u00ed\u00f3\u00fa\u00fc\u00f1\u00c1\u00c9\u00cd\u00d3\u00da\u00dc\u00d1",
        "aeiouunAEIOUUN",
    )
    return " ".join(text.translate(replacements).lower().split())
