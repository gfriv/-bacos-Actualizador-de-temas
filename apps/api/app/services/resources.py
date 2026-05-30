from app.db.models import ResourceType

RESOURCE_TITLES: dict[ResourceType, str] = {
    ResourceType.esquema_desarrollado: "Esquema desarrollado",
    ResourceType.test_autoevaluacion: "Test de autoevaluación",
    ResourceType.presentacion_clase: "Presentación estructurada",
    ResourceType.guion_audio: "Guion de audio",
    ResourceType.guion_video: "Guion de vídeo resumen",
}
