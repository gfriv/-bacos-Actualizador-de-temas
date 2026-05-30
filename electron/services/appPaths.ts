import { app } from "electron";
import path from "node:path";
import { mkdirSync } from "node:fs";
import type { DesktopPaths } from "../types/desktop";

export function getRepoRoot(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "app");
  }
  return path.resolve(__dirname, "..", "..");
}

export function getDesktopPaths(): DesktopPaths {
  const userDataDir = app.getPath("userData");
  const configDir = userDataDir;
  const dataDir = path.join(app.getPath("appData"), "AbacosIA");
  const modelsDir = path.join(dataDir, "models");
  const logsDir = path.join(dataDir, "logs");
  const uploadDir = path.join(dataDir, "storage", "uploads");
  const generatedDir = path.join(dataDir, "storage", "generated");
  for (const directory of [configDir, dataDir, modelsDir, logsDir, uploadDir, generatedDir]) {
    mkdirSync(directory, { recursive: true });
  }

  return {
    userDataDir,
    configDir,
    dataDir,
    modelsDir,
    logsDir,
    apiDatabaseUrl: `sqlite:///${path.join(dataDir, "abacos.db").replaceAll("\\", "/")}`,
    uploadDir,
    generatedDir
  };
}
