import { app, ipcMain } from "electron";
import { CHANNELS } from "./channels";
import { BackendProcessManager } from "../services/backendProcessManager";
import { detectHardware } from "../services/hardwareDetector";
import { LocalConfigStore } from "../services/localConfigStore";
import { recommendModels } from "../services/modelRecommender";
import { OllamaManager } from "../services/ollamaManager";
import { getDesktopPaths } from "../services/appPaths";
import { SecureSecretsStore } from "../services/secureStore";
import { assertSafeModelName, assertSafeSecretKey } from "../security/ipcGuards";
import type { HardwareProfile, FirstRunConfig } from "../types/desktop";

type DesktopManagers = {
  backend: BackendProcessManager;
  ollama: OllamaManager;
  config: LocalConfigStore;
  secrets: SecureSecretsStore;
};

export function registerIpcHandlers(managers: DesktopManagers): void {
  ipcMain.handle(CHANNELS.appInfo, () => ({
    name: app.getName(),
    version: app.getVersion(),
    packaged: app.isPackaged
  }));

  ipcMain.handle(CHANNELS.pathsGet, () => getDesktopPaths());
  ipcMain.handle(CHANNELS.backendStatus, () => managers.backend.status());
  ipcMain.handle(CHANNELS.backendRestart, () => managers.backend.restart());

  ipcMain.handle(CHANNELS.hardwareDetect, () => detectHardware());
  ipcMain.handle(CHANNELS.modelsRecommend, (_event, profile: HardwareProfile) =>
    recommendModels(profile)
  );

  ipcMain.handle(CHANNELS.ollamaDetect, () => managers.ollama.detectOllama());
  ipcMain.handle(CHANNELS.ollamaStart, () => managers.ollama.startOllama());
  ipcMain.handle(CHANNELS.ollamaStop, () => managers.ollama.stopOllama());
  ipcMain.handle(CHANNELS.ollamaRestart, () => managers.ollama.restartOllama());
  ipcMain.handle(CHANNELS.ollamaListModels, () => managers.ollama.listLocalModels());
  ipcMain.handle(CHANNELS.ollamaPullModel, async (event, modelName: string) => {
    assertSafeModelName(modelName);
    await managers.ollama.pullModel(modelName, (progress) => {
      event.sender.send("abacos:ollama-pull-progress", progress);
    });
    return { status: "ok" };
  });
  ipcMain.handle(CHANNELS.ollamaDeleteModel, (_event, modelName: string) => {
    assertSafeModelName(modelName);
    return managers.ollama.deleteModel(modelName);
  });
  ipcMain.handle(CHANNELS.ollamaTestModel, (_event, modelName: string) => {
    assertSafeModelName(modelName);
    return managers.ollama.testModel(modelName);
  });
  ipcMain.handle(CHANNELS.ollamaWarmupModel, (_event, modelName: string) => {
    assertSafeModelName(modelName);
    return managers.ollama.warmupModel(modelName);
  });

  ipcMain.handle(CHANNELS.configGet, () => managers.config.getConfig());
  ipcMain.handle(CHANNELS.configSet, (_event, value: { firstRun?: FirstRunConfig }) =>
    managers.config.setConfig(value)
  );

  ipcMain.handle(CHANNELS.secretSet, (_event, key: string, value: string) => {
    assertSafeSecretKey(key);
    managers.secrets.setSecret(key, value);
    return { ok: true };
  });
  ipcMain.handle(CHANNELS.secretGet, (_event, key: string) => {
    assertSafeSecretKey(key);
    return managers.secrets.getSecret(key);
  });
  ipcMain.handle(CHANNELS.secretDelete, (_event, key: string) => {
    assertSafeSecretKey(key);
    managers.secrets.deleteSecret(key);
    return { ok: true };
  });
}
