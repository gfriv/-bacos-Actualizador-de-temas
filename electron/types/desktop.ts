export type DesktopMode = "development" | "packaged";

export type BackendStatus = {
  running: boolean;
  baseUrl: string;
  pid?: number;
  error?: string;
};

export type HardwareProfile = {
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

export type ModelRecommendation = {
  modelName: string;
  displayName: string;
  family: "qwen" | "gemma" | "llama" | "mistral" | "other";
  minRamGB: number;
  recommendedRamGB: number;
  minVramGB?: number;
  estimatedDownloadGB?: number;
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

export type OllamaStatus = {
  installed: boolean;
  running: boolean;
  baseUrl: string;
  version?: string;
  installPath?: string;
  modelsPath?: string;
  error?: string;
};

export type OllamaModelInfo = {
  name: string;
  size?: number;
  family?: string;
  parameterSize?: string;
  quantization?: string;
  modifiedAt?: string;
};

export type OllamaPullProgress = {
  status: string;
  digest?: string;
  total?: number;
  completed?: number;
  percent?: number;
};

export type DesktopPaths = {
  userDataDir: string;
  configDir: string;
  dataDir: string;
  modelsDir: string;
  logsDir: string;
  apiDatabaseUrl: string;
  uploadDir: string;
  generatedDir: string;
};

export type FirstRunConfig = {
  completed: boolean;
  aiMode?: "api" | "local";
  providerId?: string;
  model?: string;
  baseUrl?: string;
  rememberSecrets?: boolean;
  modelsDir?: string;
};
