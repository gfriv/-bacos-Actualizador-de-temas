from typing import Any

import httpx

from app.core.config import settings
from app.llm.schemas import ModelConfig, ModelInfo, ProviderId, ProviderValidationResult


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model

    @property
    def configured_model(self) -> str:
        return self.model

    def _ensure_configured(self) -> None:
        if not self.base_url or not self.api_key or not self.model:
            raise RuntimeError("Base URL, API key y modelo son obligatorios para el proveedor compatible.")

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        self._ensure_configured()
        config = model_config or ModelConfig()
        payload = {
            "model": config.model or self.model,
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        text = await self.generate_text(
            prompt=f"{prompt}\n\nDevuelve JSON valido sin texto adicional.",
            system_prompt=system_prompt,
            model_config=model_config,
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

    async def list_models(self) -> list[ModelInfo]:
        if not self.base_url or not self.api_key:
            raise RuntimeError("Base URL y API key son obligatorias para listar modelos.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/models", headers=headers)
            response.raise_for_status()
        data = response.json()
        items = data.get("data", []) if isinstance(data, dict) else []
        return [
            ModelInfo(id=str(item.get("id")), display_name=str(item.get("id")))
            for item in items
            if isinstance(item, dict) and item.get("id")
        ]

    async def validate_connection(self, provider_id: ProviderId = "openai_compatible") -> ProviderValidationResult:
        models = await self.list_models()
        return ProviderValidationResult(
            ok=True,
            provider_id=provider_id,
            message="Conexion validada.",
            models=models[:20],
        )


def extract_json_payload(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.removeprefix("```json").removeprefix("```").strip()
        if clean.endswith("```"):
            clean = clean[:-3].strip()
    first_object = clean.find("{")
    last_object = clean.rfind("}")
    first_array = clean.find("[")
    last_array = clean.rfind("]")
    if first_object != -1 and last_object > first_object:
        return clean[first_object : last_object + 1]
    if first_array != -1 and last_array > first_array:
        return clean[first_array : last_array + 1]
    return clean
