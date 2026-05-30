import { readFileSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { getDesktopPaths } from "./appPaths";
import type { FirstRunConfig } from "../types/desktop";

type LocalConfig = {
  firstRun?: FirstRunConfig;
  modelsDir?: string;
};

export class LocalConfigStore {
  private readonly filePath = path.join(getDesktopPaths().configDir, "desktop-config.json");

  getConfig(): LocalConfig {
    if (!existsSync(this.filePath)) return {};
    try {
      return JSON.parse(readFileSync(this.filePath, "utf-8")) as LocalConfig;
    } catch {
      return {};
    }
  }

  setConfig(nextConfig: LocalConfig): LocalConfig {
    const current = this.getConfig();
    const merged = { ...current, ...nextConfig };
    writeFileSync(this.filePath, JSON.stringify(merged, null, 2), "utf-8");
    return merged;
  }
}
