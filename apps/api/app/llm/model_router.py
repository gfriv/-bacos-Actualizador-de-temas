from typing import Any

from app.core.config import settings
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_compatible_provider import OpenAICompatibleProvider
from app.llm.runtime_policy import assert_provider_runtime_allowed, effective_provider_config
from app.llm.schemas import AIProviderConfig, ModelConfig, ModelInfo, ProviderValidationResult


class ModelRouter:
    def __init__(self, provider_name: str | None = None, provider_config: AIProviderConfig | None = None):
        self.provider_config = provider_config
        selected = provider_config.provider_id if provider_config else provider_name or settings.llm_provider
        self.provider_id = selected
        runtime_config = provider_config or effective_provider_config(selected)
        assert_provider_runtime_allowed(runtime_config)

        if selected == "mock":
            self.provider = MockProvider()
        elif selected == "openai":
            config = provider_config or AIProviderConfig(provider_id="openai", mode="api")
            self.provider = OpenAICompatibleProvider(
                base_url=(config.base_url or "https://api.openai.com/v1"),
                api_key=config.api_key,
                model=config.model or settings.llm_model,
            )
        elif selected == "openai_compatible":
            config = provider_config or AIProviderConfig(provider_id="openai_compatible", mode="api")
            self.provider = OpenAICompatibleProvider(
                base_url=config.base_url or settings.llm_base_url,
                api_key=config.api_key or settings.llm_api_key,
                model=config.model or settings.llm_model,
            )
        elif selected == "gemini":
            config = provider_config or AIProviderConfig(provider_id="gemini", mode="api")
            self.provider = GeminiProvider(
                api_key=config.api_key or settings.llm_api_key,
                model=config.model or settings.llm_model or None,
                base_url=config.base_url,
            )
        elif selected == "anthropic":
            config = provider_config or AIProviderConfig(provider_id="anthropic", mode="api")
            self.provider = AnthropicProvider(
                api_key=config.api_key or settings.llm_api_key,
                model=config.model or settings.llm_model or None,
                base_url=config.base_url,
            )
        elif selected == "ollama":
            config = provider_config or AIProviderConfig(provider_id="ollama", mode="local")
            self.provider = OllamaProvider(
                base_url=config.base_url or settings.ollama_base_url,
                model=config.model or settings.llm_model or None,
            )
        else:
            raise ValueError(f"Proveedor LLM no soportado: {selected}")

    @property
    def model_name(self) -> str | None:
        return getattr(self.provider, "configured_model", None)

    async def validate_connection(self) -> ProviderValidationResult:
        if hasattr(self.provider, "validate_connection"):
            result = await self.provider.validate_connection()
            if result.provider_id != self.provider_id:
                result.provider_id = self.provider_id
            return result
        return ProviderValidationResult(ok=True, provider_id=self.provider_id, message="Proveedor disponible.")

    async def list_models(self) -> list[ModelInfo]:
        if hasattr(self.provider, "list_models"):
            return await self.provider.list_models()
        return [ModelInfo(id="mock", display_name="MockProvider")]

    async def generate_text(
        self, prompt: str, system_prompt: str | None = None, model_config: ModelConfig | None = None
    ) -> str:
        return await self.provider.generate_text(prompt, system_prompt, model_config)

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: type[Any] | None = None,
        model_config: ModelConfig | None = None,
    ) -> Any:
        return await self.provider.generate_json(prompt, system_prompt, schema, model_config)

    async def summarize(self, text: str, instructions: str | None = None) -> str:
        return await self.provider.summarize(text, instructions)

    async def extract_structured_data(self, text: str, schema: type[Any]) -> Any:
        return await self.provider.extract_structured_data(text, schema)

    async def generate_document_resource(self, document: str, resource_type: str) -> str:
        return await self.provider.generate_document_resource(document, resource_type)
