import { app, BrowserWindow, shell } from "electron";
import path from "node:path";
import { BackendProcessManager } from "./services/backendProcessManager";
import { FrontendProcessManager } from "./services/frontendProcessManager";
import { LocalConfigStore } from "./services/localConfigStore";
import { OllamaManager } from "./services/ollamaManager";
import { SecureSecretsStore } from "./services/secureStore";
import { registerIpcHandlers } from "./ipc/handlers";
import { redactSecrets } from "./security/secretRedaction";

const frontend = new FrontendProcessManager();
let backend: BackendProcessManager | null = null;
const ollama = new OllamaManager();
let currentRendererUrl = process.env.ABACOS_RENDERER_URL ?? "http://127.0.0.1:3000";

let mainWindow: BrowserWindow | null = null;

app.setName("Ábacos IA");

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
}

app.on("second-instance", () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

app.whenReady().then(async () => {
  const rendererUrl = await frontend.start().catch((error) => {
    console.error(redactSecrets(error));
    return currentRendererUrl;
  });
  currentRendererUrl = rendererUrl;
  backend = new BackendProcessManager(rendererUrl);

  registerIpcHandlers({
    backend,
    ollama,
    config: new LocalConfigStore(),
    secrets: new SecureSecretsStore()
  });

  createMainWindow(rendererUrl);
  try {
    await backend.start();
  } catch (error) {
    console.error(redactSecrets(error));
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow(currentRendererUrl);
  }
});

app.on("before-quit", async () => {
  await backend?.stop();
  await frontend.stop();
});

function createMainWindow(rendererUrl: string): void {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 920,
    minWidth: 1080,
    minHeight: 720,
    backgroundColor: "#F7F7F5",
    title: "Ábacos IA",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true
    }
  });

  mainWindow.webContents.session.setPermissionRequestHandler((_webContents, _permission, callback) => {
    callback(false);
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://") || url.startsWith("mailto:")) {
      void shell.openExternal(url);
    }
    return { action: "deny" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (!url.startsWith(rendererUrl)) {
      event.preventDefault();
    }
  });

  void mainWindow.loadURL(rendererUrl);
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}
