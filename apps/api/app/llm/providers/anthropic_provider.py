from typing import Any

import httpx

from app.llm.providers.openai_compatible_provider import extract_json_payload
from app.llm.schemas import ModelConfig, ModelInfo, ProviderValidationResult


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or ""
        self.model = model or "claude-3-5-haiku-latest"
        self.base_url = (base_url or "https://api.anthropic.com/v1").rstrip("/")

    @property
    def configured_model(self) -> str:
        return self.model

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("Anthropic requiere API key.")
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/models", headers=self._headers())
            response.raise_for_status()
        data = response.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [
            ModelInfo(id=str(item.get("id")), display_name=str(item.get("display_name") or item.get("id")))
            for item in items
            if isinstance(item, dict) and item.get("id")
        ]

    async def validate_connection(self) -> ProviderValidationResult:
        models = await self.list_models()
        return ProviderValidationResult(ok=True, provider_id="anthropic", message="Conexion validada.", models=models[:20])

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        config = model_config or ModelConfig()
        payload = {
            "model": config.model or self.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "system": system_prompt or "",
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/messages", headers=self._headers(), json=payload)
            response.raise_for_status()
        data = response.json()
        return "".join(str(block.get("text", "")) for block in data.get("content", []) if isinstance(block, dict))

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
