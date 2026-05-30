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
