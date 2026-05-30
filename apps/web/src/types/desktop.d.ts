export {};

type HardwareProfile = {
  os: "windows" | "macos" | "linux" | "unknown";
  arch: "x64" | "arm64" | "unknown";
  totalRamGB: number;
  freeRamGB?: number;
  cpuModel?: string;
  cpuCores?: number;
  gpuVendor?: "nvidia" | "amd" | "intel" | "apple" | "unknown" | "none";
  gpuModel?: string;
  gpuMemoryGB?: number;
  diskFreeGB?: number;
  hasNvidiaCuda?: boolean;
  hasAppleSilicon?: boolean;
};

type ModelRecommendation = {
  modelName: string;
  displayName: string;
  quality: "basic" | "medium" | "high";
  speed: "fast" | "medium" | "slow";
  suitability:
    | "api_recommended"
    | "safe_local"
    | "balanced"
    | "advanced_local"
    | "not_recommended";
  reason: string;
  warnings: string[];
};

type OllamaStatus = {
  installed: boolean;
  running: boolean;
  baseUrl: string;
  error?: string;
};

type OllamaModelInfo = {
  name: string;
  size?: number;
  family?: string;
  parameterSize?: string;
  quantization?: string;
  modifiedAt?: string;
};

type FirstRunConfig = {
  completed: boolean;
  aiMode?: "api" | "local";
  providerId?: string;
  model?: string;
  baseUrl?: string;
  rememberSecrets?: boolean;
  modelsDir?: string;
};

declare global {
  interface Window {
    abacosDesktop?: {
      isDesktop: true;
      getBackendStatus(): Promise<{ running: boolean; baseUrl: string; error?: string }>;
      restartBackend(): Promise<{ running: boolean; baseUrl: string; error?: string }>;
      detectHardware(): Promise<HardwareProfile>;
      recommendModels(profile: HardwareProfile): Promise<ModelRecommendation[]>;
      detectOllama(): Promise<OllamaStatus>;
      startOllama(): Promise<OllamaStatus>;
      listOllamaModels(): Promise<OllamaModelInfo[]>;
      pullOllamaModel(modelName: string): Promise<{ status: string }>;
      testOllamaModel(modelName: string): Promise<boolean>;
      getConfig(): Promise<{ firstRun?: FirstRunConfig }>;
      setConfig(value: { firstRun?: FirstRunConfig }): Promise<{ firstRun?: FirstRunConfig }>;
      setSecret(key: string, value: string): Promise<{ ok: boolean }>;
      getSecret(key: string): Promise<string | null>;
      deleteSecret(key: string): Promise<{ ok: boolean }>;
    };
  }
}
