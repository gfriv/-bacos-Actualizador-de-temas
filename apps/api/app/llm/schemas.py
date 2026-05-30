from typing import Any, Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["low", "medium", "high"]


class ScientificSuggestion(BaseModel):
    section_title: str
    original_fragment: str
    issue_detected: str
    proposed_change: str
    justification: str
    source_reference: str
    confidence_level: ConfidenceLevel
    needs_human_verification: bool = True


class CurriculumSuggestion(BaseModel):
    section_title: str
    curricular_connection: str
    competency_connection: str
    legal_reference: str
    proposed_change: str
    justification: str
    confidence_level: ConfidenceLevel
    needs_human_verification: bool = True


class GeneratedTestQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=2)
    correct_answer: str
    explanation: str
    difficulty: Literal["low", "medium", "high"]


class ModelConfig(BaseModel):
    temperature: float = 0.2
    max_tokens: int = 2000
    model: str | None = None


ProviderId = Literal["mock", "openai", "gemini", "anthropic", "openai_compatible", "ollama"]
ProviderMode = Literal["api", "local"]


class AIProviderConfig(BaseModel):
    provider_id: ProviderId
    mode: ProviderMode
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class ModelInfo(BaseModel):
    id: str
    display_name: str
    context_window: int | None = None
    installed: bool | None = None
    recommended: bool = False


class ProviderValidationResult(BaseModel):
    ok: bool
    provider_id: ProviderId
    message: str
    models: list[ModelInfo] = Field(default_factory=list)


class AIProviderDescriptor(BaseModel):
    id: ProviderId
    display_name: str
    mode: ProviderMode
    requires_api_key: bool = False
    supports_model_listing: bool = True
    default_base_url: str | None = None
    recommended_models: list[ModelInfo] = Field(default_factory=list)


class ProviderValidationRequest(BaseModel):
    config: AIProviderConfig


class ModelListRequest(BaseModel):
    config: AIProviderConfig


class GenerateTextInput(BaseModel):
    prompt: str
    system_prompt: str | None = None
    generation_config: ModelConfig | None = Field(default=None, alias="model_config")


class GenerateTextRequest(BaseModel):
    config: AIProviderConfig
    input: GenerateTextInput


class GenerateTextResult(BaseModel):
    text: str
    provider_id: ProviderId
    model: str | None = None


class GenerateStructuredRequest(GenerateTextRequest):
    schema_name: str | None = None
    example: dict[str, Any] | None = None


class OllamaPullRequest(BaseModel):
    model: str
    confirm: bool = False
