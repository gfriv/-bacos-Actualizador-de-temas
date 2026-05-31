from __future__ import annotations

from dataclasses import dataclass

from app.db.models import Project


@dataclass(frozen=True)
class NormativeItem:
    level: str
    title: str
    expected_source: str
    status: str
    note: str


@dataclass(frozen=True)
class NormativeContext:
    items: tuple[NormativeItem, ...]
    requires_official_validation: bool
    missing_items: tuple[str, ...]


def build_normative_context(project: Project) -> NormativeContext:
    text = _normalize(f"{project.area} {project.educational_level} {project.legal_framework}")
    items: list[NormativeItem] = [
        NormativeItem(
            level="state_law",
            title="LOMLOE/LOE vigente",
            expected_source="boe.es",
            status="provided" if "lomloe" in text or "loe" in text else "missing",
            note="Marco estatal general que debe contrastarse en BOE.",
        )
    ]
    stage = _stage(text)
    if stage:
        items.append(
            NormativeItem(
                level="state_curriculum",
                title=f"Real Decreto estatal de {stage}",
                expected_source="boe.es",
                status="provided" if "real decreto" in text or "boe" in text or "lomloe" in text else "missing",
                note="Base minima estatal; no sustituye normativa autonomica.",
            )
        )
    if _is_extremadura(text):
        items.append(
            NormativeItem(
                level="regional_curriculum",
                title=f"Decreto curricular de Extremadura para {stage or 'la etapa'}",
                expected_source="doe.juntaex.es",
                status="provided" if "decreto" in text or "doe" in text else "missing",
                note="Debe verificarse en DOE/Junta de Extremadura.",
            )
        )
        items.append(
            NormativeItem(
                level="regional_evaluation",
                title="Orden o instruccion de evaluacion de Extremadura",
                expected_source="doe.juntaex.es",
                status="provided" if "orden" in text or "evaluacion" in text else "missing",
                note="Necesaria si el tema formula evaluacion, promocion o calificacion.",
            )
        )
    if "oposicion" in text or "oposiciones" in text:
        items.append(
            NormativeItem(
                level="opposition_access",
                title="Reglamento estatal de ingreso docente",
                expected_source="boe.es",
                status="provided" if "276/2007" in text or "ingreso" in text else "missing",
                note="Marco estatal de acceso; debe completarse con convocatoria.",
            )
        )
        items.append(
            NormativeItem(
                level="opposition_call",
                title="Convocatoria autonomica concreta",
                expected_source="diario oficial autonomico",
                status="provided" if "convocatoria" in text else "missing",
                note="Sin convocatoria concreta no deben cerrarse requisitos especificos.",
            )
        )

    missing = tuple(item.level for item in items if item.status == "missing")
    return NormativeContext(
        items=tuple(items),
        requires_official_validation=bool(items),
        missing_items=missing,
    )


def format_normative_context_markdown(context: NormativeContext) -> str:
    if not context.items:
        return "- No se ha podido construir jerarquia normativa."
    lines = []
    for item in context.items:
        lines.append(
            f"- **{item.level}** · {item.status}: {item.title}. "
            f"Fuente esperada: {item.expected_source}. {item.note}"
        )
    return "\n".join(lines)


def _stage(text: str) -> str | None:
    if "infantil" in text:
        return "Educacion Infantil"
    if "primaria" in text:
        return "Educacion Primaria"
    if "eso" in text or "secundaria" in text:
        return "Educacion Secundaria Obligatoria"
    if "bachiller" in text:
        return "Bachillerato"
    if "fp" in text or "formacion profesional" in text:
        return "Formacion Profesional"
    return None


def _is_extremadura(text: str) -> bool:
    return any(marker in text for marker in ("extremadura", "juntaex", "educarex", "doe.juntaex"))


def _normalize(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(text.translate(replacements).lower().split())
