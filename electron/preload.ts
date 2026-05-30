import { contextBridge, ipcRenderer } from "electron";
import { CHANNELS } from "./ipc/channels";
import { assertAllowedChannel } from "./security/ipcGuards";
import type {
  FirstRunConfig,
  HardwareProfile,
  ModelRecommendation,
  OllamaModelInfo,
  OllamaPullProgress,
  OllamaStatus
} from "./types/desktop";

function invoke<T>(channel: string, ...args: unknown[]): Promise<T> {
  assertAllowedChannel(channel);
  return ipcRenderer.invoke(channel, ...args) as Promise<T>;
}

contextBridge.exposeInMainWorld("abacosDesktop", {
  isDesktop: true,
  getAppInfo: () => invoke(CHANNELS.appInfo),
  getPaths: () => invoke(CHANNELS.pathsGet),
  getBackendStatus: () => invoke(CHANNELS.backendStatus),
  restartBackend: () => invoke(CHANNELS.backendRestart),
  detectHardware: () => invoke<HardwareProfile>(CHANNELS.hardwareDetect),
  recommendModels: (profile: HardwareProfile) =>
    invoke<ModelRecommendation[]>(CHANNELS.modelsRecommend, profile),
  detectOllama: () => invoke<OllamaStatus>(CHANNELS.ollamaDetect),
  startOllama: () => invoke<OllamaStatus>(CHANNELS.ollamaStart),
  stopOllama: () => invoke<void>(CHANNELS.ollamaStop),
  restartOllama: () => invoke<OllamaStatus>(CHANNELS.ollamaRestart),
  listOllamaModels: () => invoke<OllamaModelInfo[]>(CHANNELS.ollamaListModels),
  pullOllamaModel: (modelName: string) => invoke<{ status: string }>(CHANNELS.ollamaPullModel, modelName),
  deleteOllamaModel: (modelName: string) => invoke<void>(CHANNELS.ollamaDeleteModel, modelName),
  testOllamaModel: (modelName: string) => invoke<boolean>(CHANNELS.ollamaTestModel, modelName),
  warmupOllamaModel: (modelName: string) => invoke<void>(CHANNELS.ollamaWarmupModel, modelName),
  onOllamaPullProgress: (callback: (progress: OllamaPullProgress) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, progress: OllamaPullProgress) => callback(progress);
    ipcRenderer.on("abacos:ollama-pull-progress", listener);
    return () => ipcRenderer.removeListener("abacos:ollama-pull-progress", listener);
  },
  getConfig: () => invoke(CHANNELS.configGet),
  setConfig: (value: { firstRun?: FirstRunConfig }) => invoke(CHANNELS.configSet, value),
  setSecret: (key: string, value: string) => invoke(CHANNELS.secretSet, key, value),
  getSecret: (key: string) => invoke<string | null>(CHANNELS.secretGet, key),
  deleteSecret: (key: string) => invoke(CHANNELS.secretDelete, key)
});
