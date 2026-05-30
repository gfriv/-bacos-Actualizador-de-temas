from typing import Any

import httpx

from app.llm.providers.openai_compatible_provider import extract_json_payload
from app.llm.schemas import ModelConfig, ModelInfo, ProviderValidationResult


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or ""
        self.model = model or "gemini-1.5-flash"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

    @property
    def configured_model(self) -> str:
        return self.model

    def _ensure_configured(self) -> None:
        if not self.api_key or not self.model:
            raise RuntimeError("Gemini requiere API key y modelo.")

    async def list_models(self) -> list[ModelInfo]:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/models", params={"key": self.api_key})
            response.raise_for_status()
        data = response.json()
        models = data.get("models", []) if isinstance(data, dict) else []
        return [
            ModelInfo(
                id=str(item.get("name", "")).removeprefix("models/"),
                display_name=str(item.get("displayName") or item.get("name")),
            )
            for item in models
            if isinstance(item, dict) and item.get("name")
        ]

    async def validate_connection(self) -> ProviderValidationResult:
        models = await self.list_models()
        return ProviderValidationResult(ok=True, provider_id="gemini", message="Conexion validada.", models=models[:20])

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        self._ensure_configured()
        config = model_config or ModelConfig()
        text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_tokens,
            },
        }
        model = config.model or self.model
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent",
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        text = await self.generate_text(f"{prompt}\n\nDevuelve JSON valido sin texto adicional.", system_prompt, model_config)
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
