from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LegalFrameworkOption:
    id: str
    label: str
    value: str
    description: str


LEGAL_FRAMEWORK_OPTIONS: tuple[LegalFrameworkOption, ...] = (
    LegalFrameworkOption(
        id="auto",
        label="Inferencia automática por etapa",
        value="",
        description="El sistema propone el marco normativo inicial desde área, nivel y fuentes oficiales recuperadas.",
    ),
    LegalFrameworkOption(
        id="extremadura_infantil",
        label="Extremadura · Educación Infantil",
        value=(
            "LOMLOE, Real Decreto 95/2022, Ley 4/2011 de Educación de Extremadura, "
            "Decreto 98/2022 de Educación Infantil de Extremadura, evaluación autonómica y convocatoria aplicable."
        ),
        description="Marco inicial para temas o supuestos de Infantil en Extremadura.",
    ),
    LegalFrameworkOption(
        id="extremadura_primaria",
        label="Extremadura · Educación Primaria",
        value=(
            "LOMLOE, Real Decreto 157/2022, Ley 4/2011 de Educación de Extremadura, "
            "Decreto 107/2022 de Educación Primaria de Extremadura, evaluación autonómica y convocatoria aplicable."
        ),
        description="Marco inicial para temas o supuestos de Primaria en Extremadura.",
    ),
    LegalFrameworkOption(
        id="extremadura_secundaria",
        label="Extremadura · ESO/Bachillerato",
        value=(
            "LOMLOE, Real Decreto 217/2022 de ESO, Real Decreto 243/2022 de Bachillerato, "
            "Ley 4/2011 de Educación de Extremadura, Decretos curriculares autonómicos vigentes, "
            "evaluación autonómica y convocatoria aplicable."
        ),
        description="Marco inicial para Secundaria y Bachillerato en Extremadura.",
    ),
    LegalFrameworkOption(
        id="estatal_oposiciones",
        label="Estatal · Oposiciones docentes",
        value=(
            "LOMLOE/LOE vigente, currículo estatal de la etapa, Real Decreto 276/2007 de ingreso docente, "
            "convocatoria autonómica aplicable y normativa curricular autonómica vigente."
        ),
        description="Base estatal para oposiciones; debe completarse con la comunidad autónoma concreta.",
    ),
)


def legal_framework_catalog() -> list[dict[str, str]]:
    return [option.__dict__.copy() for option in LEGAL_FRAMEWORK_OPTIONS]


def infer_legal_framework(*, area: str, educational_level: str, instructions: str | None = None) -> str:
    text = _normalize(f"{area} {educational_level} {instructions or ''}")
    parts: list[str] = ["Marco normativo inferido automáticamente; requiere verificación docente."]
    parts.append("LOMLOE/LOE vigente y currículo estatal de la etapa.")

    if "infantil" in text:
        parts.append("Real Decreto 95/2022 para Educación Infantil.")
    elif "primaria" in text:
        parts.append("Real Decreto 157/2022 para Educación Primaria.")
    elif "eso" in text or "secundaria" in text:
        parts.append("Real Decreto 217/2022 para Educación Secundaria Obligatoria.")
    elif "bachiller" in text:
        parts.append("Real Decreto 243/2022 para Bachillerato.")
    elif "fp" in text or "formacion profesional" in text:
        parts.append("Normativa estatal de Formación Profesional vigente y desarrollo autonómico aplicable.")
    else:
        parts.append("Etapa no determinada con seguridad; el informe curricular debe priorizar fuentes oficiales recuperadas.")

    if "oposicion" in text or "oposiciones" in text or "tribunal" in text:
        parts.append("Real Decreto 276/2007 de ingreso docente y convocatoria autonómica aplicable.")

    if "extremadura" in text or "caceres" in text or "badajoz" in text or "juntaex" in text or "educarex" in text:
        parts.append("Ley 4/2011 de Educación de Extremadura, DOE/Educarex y decreto curricular autonómico correspondiente.")
    else:
        parts.append("Normativa autonómica aplicable según comunidad; si el usuario no indica comunidad, se marcará como aspecto a verificar.")

    return " ".join(parts)


def resolve_legal_framework(*, area: str, educational_level: str, legal_framework: str | None, instructions: str | None) -> str:
    cleaned = (legal_framework or "").strip()
    return cleaned if cleaned else infer_legal_framework(area=area, educational_level=educational_level, instructions=instructions)


def _normalize(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(text.translate(replacements).lower().split())
