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
            "Requiere revisión docente antes de cualquier consolidación."
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        data = {
            "section_title": "Introducción",
            "original_fragment": "Referencia o formulación que debe revisarse.",
            "issue_detected": "Posible desactualización o falta de contexto normativo.",
            "proposed_change": "Actualizar de forma localizada y marcar para revisión docente.",
            "justification": "Propuesta simulada para validar el flujo del MVP.",
            "source_reference": "MockProvider; requiere fuente real antes de aprobación.",
            "confidence_level": "medium",
            "needs_human_verification": True,
        }
        return schema.model_validate(data) if schema else data

    async def summarize(self, text: str, instructions: str | None = None) -> str:
        return f"Resumen simulado: {text[:220]}"

    async def extract_structured_data(self, text: str, schema: type[Any]) -> Any:
        return await self.generate_json(text, schema=schema)

    async def generate_document_resource(self, document: str, resource_type: str) -> str:
        return (
            f"# {resource_type.replace('_', ' ').title()}\n\n"
            "Recurso didáctico simulado generado desde el documento consolidado.\n\n"
            "- Mantiene alineación conceptual.\n"
            "- No añade contenido científico nuevo.\n"
            "- Requiere revisión docente antes de uso final."
        )
