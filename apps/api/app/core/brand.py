from __future__ import annotations

from datetime import UTC, datetime

ABACOS_LEGAL_NAME = "Centro de Formación y Estudios Ábacos"
ABACOS_SHORT_NAME = "Ábacos"
ABACOS_ADDRESS = "Avda. Virgen de Guadalupe, 33, 4ª planta. 10001 Cáceres"
ABACOS_PHONE = "927 24 50 50"
ABACOS_MOBILE = "648 91 84 11"
ABACOS_EMAIL = "consultasabacos@gmail.com"
ABACOS_SCHEDULE = "Lunes a viernes, de 17:00 a 21:00"
ABACOS_SOURCE_URL = "https://academiaabaco.net/contacto"
ABACOS_AREAS = ("Educación", "Sanidad", "JuntaEx", "Seguridad")

AI_ASSISTANCE_NOTICE = (
    "Este contenido se ha generado con asistencia de IA para apoyar la revisión docente. "
    "No sustituye la validación profesional del profesor ni la comprobación de fuentes."
)

HUMAN_REVIEW_RULE = (
    "La IA propone; el profesor valida. El sistema solo consolida cambios aprobados o editados."
)


def generated_at_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def build_artifact_header(
    *,
    title: str,
    project_title: str,
    generated_at: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    provider_line = provider or "mock"
    model_line = model or "no indicado"
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- Proyecto: **{project_title}**",
            f"- Fecha de generación: **{generated_at or generated_at_iso()}**",
            f"- Proveedor de IA: **{provider_line}**",
            f"- Modelo: **{model_line}**",
            f"- Regla de revisión: {HUMAN_REVIEW_RULE}",
        ]
    )


def build_ai_notice() -> str:
    return f"## Aviso de asistencia de IA\n\n{AI_ASSISTANCE_NOTICE}"


def build_corporate_footer() -> str:
    areas = ", ".join(ABACOS_AREAS)
    return (
        "## Datos del centro\n\n"
        f"- {ABACOS_LEGAL_NAME}\n"
        f"- Dirección: {ABACOS_ADDRESS}\n"
        f"- Teléfono: {ABACOS_PHONE} · Móvil: {ABACOS_MOBILE}\n"
        f"- Horario habitual: {ABACOS_SCHEDULE}\n"
        f"- Email: {ABACOS_EMAIL}\n"
        f"- Áreas de preparación: {areas}\n"
        f"- Fuente corporativa: {ABACOS_SOURCE_URL}"
    )
