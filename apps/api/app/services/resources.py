from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.brand import (
    build_ai_notice,
    build_artifact_header,
    build_corporate_footer,
    generated_at_iso,
)
from app.db.models import ResourceType

RESOURCE_TITLES: dict[ResourceType, str] = {
    ResourceType.esquema_desarrollado: "Esquema desarrollado",
    ResourceType.test_autoevaluacion: "Test de autoevaluación",
    ResourceType.presentacion_clase: "Presentación estructurada",
    ResourceType.guion_audio: "Guion de audio",
    ResourceType.guion_video: "Guion de vídeo resumen",
}


@dataclass(frozen=True)
class BlueprintSection:
    title: str
    content: str
    key_terms: tuple[str, ...]


@dataclass(frozen=True)
class DocumentBlueprint:
    title: str
    sections: tuple[BlueprintSection, ...]
    key_terms: tuple[str, ...]


HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
WORD_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b")


def build_document_blueprint(markdown: str) -> DocumentBlueprint:
    headings = list(HEADING_PATTERN.finditer(markdown or ""))
    if not headings:
        content = markdown.strip()
        title = "Documento consolidado"
        section = BlueprintSection(title=title, content=content, key_terms=tuple(_key_terms(content)))
        return DocumentBlueprint(title=title, sections=(section,), key_terms=section.key_terms)

    title = headings[0].group(2).strip()
    sections: list[BlueprintSection] = []
    for index, heading in enumerate(headings):
        heading_text = heading.group(2).strip()
        if index == 0 and heading.group(1) == "#":
            continue
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(markdown)
        content = markdown[start:end].strip()
        if not content:
            continue
        sections.append(
            BlueprintSection(
                title=heading_text,
                content=content,
                key_terms=tuple(_key_terms(f"{heading_text} {content}")),
            )
        )
    if not sections:
        remaining = markdown[headings[0].end() :].strip()
        sections.append(BlueprintSection(title=title, content=remaining, key_terms=tuple(_key_terms(remaining))))
    key_terms = tuple(dict.fromkeys(term for section in sections for term in section.key_terms))[:18]
    return DocumentBlueprint(title=title, sections=tuple(sections), key_terms=key_terms)


def build_resource_prompt_context(document: str, resource_type: str) -> str:
    blueprint = build_document_blueprint(document)
    section_map = "\n".join(
        f"- {section.title}: conceptos clave {', '.join(section.key_terms[:6]) or 'sin conceptos extraidos'}"
        for section in blueprint.sections[:12]
    )
    return (
        "Genera el recurso exclusivamente desde el documento consolidado y su estructura.\n"
        f"Tipo de recurso: {resource_type}.\n"
        f"Titulo del documento: {blueprint.title}.\n"
        "Mapa estructural:\n"
        f"{section_map}\n\n"
        "Reglas:\n"
        "- No introduzcas contenido cientifico nuevo no presente en el consolidado.\n"
        "- Si propones una ampliacion, marcala como ampliacion opcional.\n"
        "- Mantén español de España y tono docente profesional.\n"
        "- Incluye soluciones y explicaciones cuando el recurso sea un test."
    )


def decorate_resource_markdown(
    *,
    content: str,
    title: str,
    project_title: str,
    provider: str,
    model: str | None,
) -> str:
    return "\n\n".join(
        [
            build_artifact_header(
                title=title,
                project_title=project_title,
                generated_at=generated_at_iso(),
                provider=provider,
                model=model,
            ),
            content,
            build_ai_notice(),
            build_corporate_footer(),
        ]
    )


def _key_terms(text: str) -> list[str]:
    normalized = _normalize(text)
    stop = {
        "para",
        "como",
        "este",
        "esta",
        "tema",
        "documento",
        "consolidado",
        "desde",
        "entre",
        "sobre",
        "solo",
        "sugerencia",
        "cambios",
        "asistencia",
    }
    return [word for word in dict.fromkeys(WORD_PATTERN.findall(normalized)) if word not in stop][:12]


def _normalize(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(text.translate(replacements).lower().split())
