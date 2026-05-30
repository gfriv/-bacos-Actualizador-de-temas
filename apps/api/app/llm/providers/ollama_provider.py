from typing import Any

import httpx

from app.llm.providers.openai_compatible_provider import extract_json_payload
from app.llm.schemas import ModelConfig, ModelInfo, ProviderValidationResult


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.model = model or ""

    @property
    def configured_model(self) -> str:
        return self.model

    def _ensure_configured(self) -> None:
        if not self.base_url or not self.model:
            raise RuntimeError("Ollama requiere base URL y modelo instalado seleccionado.")

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
        data = response.json()
        models = data.get("models", []) if isinstance(data, dict) else []
        return [
            ModelInfo(
                id=str(item.get("name")),
                display_name=str(item.get("name")),
                installed=True,
            )
            for item in models
            if isinstance(item, dict) and item.get("name")
        ]

    async def validate_connection(self) -> ProviderValidationResult:
        models = await self.list_models()
        return ProviderValidationResult(
            ok=True,
            provider_id="ollama",
            message="Ollama disponible.",
            models=models,
        )

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        self._ensure_configured()
        config = model_config or ModelConfig()
        payload = {
            "model": config.model or self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
        data = response.json()
        return str(data.get("response", ""))

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        text = await self.generate_text(
            f"{prompt}\n\nDevuelve JSON valido sin texto adicional.",
            system_prompt,
            model_config,
        )
        if schema is None:
            return text
        return schema.model_validate_json(extract_json_payload(text))

    async def summarize(self, text: str, instructions: str | None = None) -> str:
        return await self.generate_text(text, instructions or "Resume el texto de forma fiel y breve.")

    async def extract_structured_data(self, text: str, schema: type[Any]) -> Any:
        return await self.generate_json(text, schema=schema)

    async def generate_document_resource(self, document: str, resource_type: str) -> str:
        return await self.generate_text(
            document,
            f"Genera un recurso didactico de tipo {resource_type} desde el documento consolidado.",
        )

    async def pull_model(self, model: str) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(f"{self.base_url}/api/pull", json={"name": model, "stream": False})
            response.raise_for_status()
        return {"status": "ok", "model": model}
