export const CHANNELS = {
  appInfo: "abacos:app-info",
  backendStatus: "abacos:backend-status",
  backendRestart: "abacos:backend-restart",
  pathsGet: "abacos:paths-get",
  hardwareDetect: "abacos:hardware-detect",
  modelsRecommend: "abacos:models-recommend",
  ollamaDetect: "abacos:ollama-detect",
  ollamaStart: "abacos:ollama-start",
  ollamaStop: "abacos:ollama-stop",
  ollamaRestart: "abacos:ollama-restart",
  ollamaListModels: "abacos:ollama-list-models",
  ollamaPullModel: "abacos:ollama-pull-model",
  ollamaDeleteModel: "abacos:ollama-delete-model",
  ollamaTestModel: "abacos:ollama-test-model",
  ollamaWarmupModel: "abacos:ollama-warmup-model",
  configGet: "abacos:config-get",
  configSet: "abacos:config-set",
  secretSet: "abacos:secret-set",
  secretGet: "abacos:secret-get",
  secretDelete: "abacos:secret-delete"
} as const;

export type DesktopChannel = (typeof CHANNELS)[keyof typeof CHANNELS];
