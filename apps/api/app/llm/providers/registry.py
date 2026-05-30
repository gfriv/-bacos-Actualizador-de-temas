from app.llm.schemas import AIProviderDescriptor, ModelInfo

RECOMMENDED_OLLAMA_MODELS = [
    ModelInfo(id="qwen2.5:7b-instruct", display_name="Qwen 2.5 7B Instruct", recommended=True),
    ModelInfo(id="qwen2.5:14b-instruct", display_name="Qwen 2.5 14B Instruct", recommended=True),
    ModelInfo(id="gemma2:9b", display_name="Gemma 2 9B", recommended=True),
    ModelInfo(id="llama3.1:8b", display_name="Llama 3.1 8B", recommended=True),
]

PROVIDER_DESCRIPTORS = [
    AIProviderDescriptor(
        id="mock",
        display_name="MockProvider",
        mode="local",
        supports_model_listing=False,
        recommended_models=[ModelInfo(id="mock", display_name="MockProvider")],
    ),
    AIProviderDescriptor(
        id="openai",
        display_name="OpenAI",
        mode="api",
        requires_api_key=True,
        default_base_url="https://api.openai.com/v1",
        recommended_models=[
            ModelInfo(id="gpt-4.1-mini", display_name="GPT-4.1 mini", recommended=True),
            ModelInfo(id="gpt-4o-mini", display_name="GPT-4o mini", recommended=True),
        ],
    ),
    AIProviderDescriptor(
        id="gemini",
        display_name="Google Gemini",
        mode="api",
        requires_api_key=True,
        recommended_models=[
            ModelInfo(id="gemini-1.5-flash", display_name="Gemini 1.5 Flash", recommended=True),
            ModelInfo(id="gemini-1.5-pro", display_name="Gemini 1.5 Pro", recommended=True),
        ],
    ),
    AIProviderDescriptor(
        id="anthropic",
        display_name="Claude / Anthropic",
        mode="api",
        requires_api_key=True,
        default_base_url="https://api.anthropic.com/v1",
        recommended_models=[
            ModelInfo(id="claude-3-5-haiku-latest", display_name="Claude 3.5 Haiku", recommended=True),
            ModelInfo(id="claude-3-5-sonnet-latest", display_name="Claude 3.5 Sonnet", recommended=True),
        ],
    ),
    AIProviderDescriptor(
        id="openai_compatible",
        display_name="OpenAI-compatible",
        mode="api",
        requires_api_key=True,
        recommended_models=[ModelInfo(id="custom-model", display_name="Modelo compatible configurado")],
    ),
    AIProviderDescriptor(
        id="ollama",
        display_name="Ollama local",
        mode="local",
        default_base_url="http://localhost:11434",
        recommended_models=RECOMMENDED_OLLAMA_MODELS,
    ),
]
