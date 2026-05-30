export type AIProviderMode = "api" | "local";

export type AIProviderId =
  | "mock"
  | "openai"
  | "gemini"
  | "anthropic"
  | "openai_compatible"
  | "ollama";

export type AIProviderConfig = {
  providerId: AIProviderId;
  mode: AIProviderMode;
  apiKey?: string;
  baseUrl?: string;
  model?: string;
};

export type BackendAIProviderConfig = {
  provider_id: AIProviderId;
  mode: AIProviderMode;
  api_key?: string | null;
  base_url?: string | null;
  model?: string | null;
};

export const AI_CONFIG_STORAGE_KEY = "abacos_ai_provider_config";
export const AI_CONFIG_CHANGED_EVENT = "abacos-ai-config-changed";

export function toBackendAIConfig(config: AIProviderConfig): BackendAIProviderConfig {
  return {
    provider_id: config.providerId,
    mode: config.mode,
    api_key: config.apiKey || null,
    base_url: config.baseUrl || null,
    model: config.model || null,
  };
}

export function toFrontendAIConfig(config: BackendAIProviderConfig): AIProviderConfig {
  return {
    providerId: config.provider_id,
    mode: config.mode,
    apiKey: config.api_key ?? undefined,
    baseUrl: config.base_url ?? undefined,
    model: config.model ?? undefined,
  };
}

export function getStoredAIConfig(): AIProviderConfig | null {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(AI_CONFIG_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AIProviderConfig;
  } catch {
    window.sessionStorage.removeItem(AI_CONFIG_STORAGE_KEY);
    return null;
  }
}

export function setStoredAIConfig(config: AIProviderConfig): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(AI_CONFIG_STORAGE_KEY, JSON.stringify(config));
  window.dispatchEvent(new Event(AI_CONFIG_CHANGED_EVENT));
}

export function clearStoredAIConfig(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(AI_CONFIG_STORAGE_KEY);
  window.dispatchEvent(new Event(AI_CONFIG_CHANGED_EVENT));
}

export function getAIConfigHeader(): string | null {
  const config = getStoredAIConfig();
  if (!config) return null;
  return encodeBase64Url(JSON.stringify(toBackendAIConfig(config)));
}

export function describeAIConfig(config: AIProviderConfig | null): string {
  if (!config) return "MockProvider";
  if (config.providerId === "ollama") return `Ollama${config.model ? ` · ${config.model}` : ""}`;
  if (config.providerId === "openai_compatible") {
    return `OpenAI-compatible${config.model ? ` · ${config.model}` : ""}`;
  }
  return `${providerLabel(config.providerId)}${config.model ? ` · ${config.model}` : ""}`;
}

export function providerLabel(providerId: AIProviderId): string {
  const labels: Record<AIProviderId, string> = {
    mock: "MockProvider",
    openai: "OpenAI",
    gemini: "Gemini",
    anthropic: "Claude",
    openai_compatible: "OpenAI-compatible",
    ollama: "Ollama",
  };
  return labels[providerId];
}

function encodeBase64Url(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return window.btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}
