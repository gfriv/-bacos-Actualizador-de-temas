export type AIProviderMode = "api" | "local";

export type AIProviderId = "mock" | "openai" | "gemini" | "anthropic" | "openai_compatible" | "ollama";

export type ProviderValidationResult = {
  ok: boolean;
  providerId: AIProviderId;
  message: string;
  models?: ModelInfo[];
};

export type ModelInfo = {
  id: string;
  displayName: string;
  contextWindow?: number;
  installed?: boolean;
  recommended?: boolean;
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
  model?: string;
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
