import { apiFetch } from "@/lib/api";
import {
  type AIProviderConfig,
  type AIProviderId,
  type AIProviderMode,
  toBackendAIConfig,
} from "@/lib/ai/config";

export type ModelInfo = {
  id: string;
  displayName: string;
  contextWindow?: number | null;
  installed?: boolean | null;
  recommended?: boolean;
};

export type ProviderValidationResult = {
  ok: boolean;
  providerId: AIProviderId;
  message: string;
  models: ModelInfo[];
};

export type AIProviderDescriptor = {
  id: AIProviderId;
  displayName: string;
  mode: AIProviderMode;
  requiresApiKey: boolean;
  supportsModelListing: boolean;
  defaultBaseUrl?: string | null;
  recommendedModels: ModelInfo[];
};

export type ModelConfig = {
  model?: string;
  temperature?: number;
  maxTokens?: number;
};

export type GenerateTextInput = {
  prompt: string;
  systemPrompt?: string;
  modelConfig?: ModelConfig;
};

export type GenerateTextResult = {
  text: string;
  providerId: AIProviderId;
  model?: string | null;
};

export type GenerateStructuredInput<T> = GenerateTextInput & {
  schemaName?: string;
  example?: T;
};

export interface AIProvider {
  id: string;
  displayName: string;
  mode: AIProviderMode;
  validateConnection(): Promise<ProviderValidationResult>;
  listModels(): Promise<ModelInfo[]>;
  generateText(input: GenerateTextInput): Promise<GenerateTextResult>;
  generateStructured<T>(input: GenerateStructuredInput<T>): Promise<T>;
  streamText?(input: GenerateTextInput): AsyncIterable<string>;
}

type BackendModelInfo = {
  id: string;
  display_name: string;
  context_window?: number | null;
  installed?: boolean | null;
  recommended?: boolean;
};

type BackendProviderDescriptor = {
  id: AIProviderId;
  display_name: string;
  mode: AIProviderMode;
  requires_api_key: boolean;
  supports_model_listing: boolean;
  default_base_url?: string | null;
  recommended_models?: BackendModelInfo[];
};

type BackendValidationResult = {
  ok: boolean;
  provider_id: AIProviderId;
  message: string;
  models?: BackendModelInfo[];
};

export const FALLBACK_AI_PROVIDERS: AIProviderDescriptor[] = [
  {
    id: "mock",
    displayName: "MockProvider",
    mode: "local",
    requiresApiKey: false,
    supportsModelListing: false,
    recommendedModels: [{ id: "mock", displayName: "MockProvider", recommended: true }],
  },
  {
    id: "openai",
    displayName: "OpenAI",
    mode: "api",
    requiresApiKey: true,
    supportsModelListing: true,
    defaultBaseUrl: "https://api.openai.com/v1",
    recommendedModels: [{ id: "gpt-4.1-mini", displayName: "GPT-4.1 mini", recommended: true }],
  },
  {
    id: "gemini",
    displayName: "Google Gemini",
    mode: "api",
    requiresApiKey: true,
    supportsModelListing: true,
    recommendedModels: [{ id: "gemini-1.5-flash", displayName: "Gemini Flash", recommended: true }],
  },
  {
    id: "anthropic",
    displayName: "Claude / Anthropic",
    mode: "api",
    requiresApiKey: true,
    supportsModelListing: true,
    defaultBaseUrl: "https://api.anthropic.com/v1",
    recommendedModels: [
      { id: "claude-3-5-haiku-latest", displayName: "Claude Haiku", recommended: true },
    ],
  },
  {
    id: "openai_compatible",
    displayName: "OpenAI-compatible",
    mode: "api",
    requiresApiKey: true,
    supportsModelListing: true,
    recommendedModels: [
      { id: "custom-model", displayName: "Modelo configurado", recommended: true },
    ],
  },
  {
    id: "ollama",
    displayName: "Ollama local",
    mode: "local",
    requiresApiKey: false,
    supportsModelListing: true,
    defaultBaseUrl: "http://localhost:11434",
    recommendedModels: [
      { id: "qwen2.5:7b-instruct", displayName: "Qwen 2.5 7B Instruct", recommended: true },
      { id: "gemma2:9b", displayName: "Gemma 2 9B", recommended: true },
      { id: "llama3.1:8b", displayName: "Llama 3.1 8B", recommended: true },
    ],
  },
];

export async function listAIProviderDescriptors(): Promise<AIProviderDescriptor[]> {
  try {
    const descriptors = await apiFetch<BackendProviderDescriptor[]>("/ai/providers");
    return descriptors.map(fromBackendDescriptor);
  } catch {
    return FALLBACK_AI_PROVIDERS;
  }
}

export function createAIProvider(
  config: AIProviderConfig,
  descriptor?: AIProviderDescriptor,
): AIProvider {
  return new BackendAIProvider(config, descriptor);
}

export async function pullOllamaModel(
  model: string,
  confirm: boolean,
): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/ai/ollama/pull", {
    method: "POST",
    body: JSON.stringify({ model, confirm }),
  });
}

class BackendAIProvider implements AIProvider {
  id: string;
  displayName: string;
  mode: AIProviderMode;

  constructor(
    private readonly config: AIProviderConfig,
    descriptor?: AIProviderDescriptor,
  ) {
    this.id = config.providerId;
    this.displayName = descriptor?.displayName ?? config.providerId;
    this.mode = config.mode;
  }

  async validateConnection(): Promise<ProviderValidationResult> {
    const result = await apiFetch<BackendValidationResult>("/ai/providers/validate", {
      method: "POST",
      body: JSON.stringify({ config: toBackendAIConfig(this.config) }),
    });
    return fromBackendValidation(result);
  }

  async listModels(): Promise<ModelInfo[]> {
    const result = await apiFetch<{ models: BackendModelInfo[] }>("/ai/providers/models", {
      method: "POST",
      body: JSON.stringify({ config: toBackendAIConfig(this.config) }),
    });
    return result.models.map(fromBackendModel);
  }

  async generateText(input: GenerateTextInput): Promise<GenerateTextResult> {
    const result = await apiFetch<{
      text: string;
      provider_id: AIProviderId;
      model?: string | null;
    }>("/ai/generate-text", {
      method: "POST",
      body: JSON.stringify({
        config: toBackendAIConfig(this.config),
        input: toBackendGenerateTextInput(input),
      }),
    });
    return { text: result.text, providerId: result.provider_id, model: result.model };
  }

  async generateStructured<T>(input: GenerateStructuredInput<T>): Promise<T> {
    const result = await apiFetch<{ raw: string }>("/ai/generate-structured", {
      method: "POST",
      body: JSON.stringify({
        config: toBackendAIConfig(this.config),
        schema_name: input.schemaName,
        example: input.example,
        input: toBackendGenerateTextInput(input),
      }),
    });
    return JSON.parse(result.raw) as T;
  }
}

function toBackendGenerateTextInput(input: GenerateTextInput) {
  return {
    prompt: input.prompt,
    system_prompt: input.systemPrompt ?? null,
    model_config: input.modelConfig
      ? {
          model: input.modelConfig.model ?? null,
          temperature: input.modelConfig.temperature,
          max_tokens: input.modelConfig.maxTokens,
        }
      : null,
  };
}

function fromBackendDescriptor(value: BackendProviderDescriptor): AIProviderDescriptor {
  return {
    id: value.id,
    displayName: value.display_name,
    mode: value.mode,
    requiresApiKey: value.requires_api_key,
    supportsModelListing: value.supports_model_listing,
    defaultBaseUrl: value.default_base_url,
    recommendedModels: (value.recommended_models ?? []).map(fromBackendModel),
  };
}

function fromBackendValidation(value: BackendValidationResult): ProviderValidationResult {
  return {
    ok: value.ok,
    providerId: value.provider_id,
    message: value.message,
    models: (value.models ?? []).map(fromBackendModel),
  };
}

function fromBackendModel(value: BackendModelInfo): ModelInfo {
  return {
    id: value.id,
    displayName: value.display_name,
    contextWindow: value.context_window,
    installed: value.installed,
    recommended: value.recommended ?? false,
  };
}
