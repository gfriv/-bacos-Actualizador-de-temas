import { app } from "electron";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { appendFileSync, existsSync, readdirSync } from "node:fs";
import path from "node:path";
import { getDesktopPaths, getRepoRoot } from "./appPaths";
import { redactSecrets } from "../security/secretRedaction";

const FRONTEND_HOST = "127.0.0.1";
const FRONTEND_PORT = 3765;
const PACKAGED_RENDERER_URL = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;
const DEV_RENDERER_URL = process.env.ABACOS_RENDERER_URL ?? "http://127.0.0.1:3000";

export class FrontendProcessManager {
  private process: ChildProcessWithoutNullStreams | null = null;
  private lastError: string | undefined;

  async start(): Promise<string> {
    if (!app.isPackaged) return DEV_RENDERER_URL;
    if (await this.isHealthy(PACKAGED_RENDERER_URL)) return PACKAGED_RENDERER_URL;

    const serverScript = this.resolveStandaloneServer();
    const env = {
      ...process.env,
      ELECTRON_RUN_AS_NODE: "1",
      HOSTNAME: FRONTEND_HOST,
      PORT: String(FRONTEND_PORT),
      NODE_ENV: "production",
      NODE_PATH: this.buildNodePath(serverScript),
      NEXT_PUBLIC_API_URL: "http://127.0.0.1:8765/api"
    };

    this.process = spawn(process.execPath, [serverScript], {
      cwd: path.dirname(serverScript),
      env,
      windowsHide: true,
      stdio: "pipe"
    });
    this.process.stdout.on("data", (chunk) => this.log("web", chunk));
    this.process.stderr.on("data", (chunk) => this.log("web", chunk));
    this.process.once("exit", (code) => {
      this.lastError = code === 0 ? undefined : `Frontend finalizado con codigo ${code ?? "desconocido"}.`;
      this.process = null;
    });

    await this.waitUntilHealthy(PACKAGED_RENDERER_URL);
    return PACKAGED_RENDERER_URL;
  }

  async stop(): Promise<void> {
    if (this.process && !this.process.killed) {
      this.process.kill();
      await wait(1000);
    }
    this.process = null;
  }

  private resolveStandaloneServer(): string {
    const root = getRepoRoot();
    const candidates = [
      path.join(root, "apps", "web", ".next", "standalone-electron", "apps", "web", "server.js"),
      path.join(root, "apps", "web", ".next", "standalone", "apps", "web", "server.js"),
      path.join(root, "apps", "web", ".next", "standalone", "server.js")
    ];
    const serverScript = candidates.find((candidate) => existsSync(candidate));
    if (!serverScript) {
      throw new Error("No se encontro el servidor standalone de Next. Ejecuta primero desktop:build:web.");
    }
    return serverScript;
  }

  private buildNodePath(serverScript: string): string {
    const standaloneRoot = serverScript.endsWith(path.join("apps", "web", "server.js"))
      ? path.resolve(path.dirname(serverScript), "..", "..")
      : path.dirname(serverScript);
    const pnpmPackagesDir = path.join(standaloneRoot, "node_modules", ".pnpm");
    const packageDirs = existsSync(pnpmPackagesDir)
      ? readdirSync(pnpmPackagesDir, { withFileTypes: true })
          .filter((entry) => entry.isDirectory())
          .map((entry) => path.join(pnpmPackagesDir, entry.name, "node_modules"))
      : [];
    return [process.env.NODE_PATH, ...packageDirs].filter(Boolean).join(path.delimiter);
  }

  private async waitUntilHealthy(url: string): Promise<void> {
    for (let attempt = 0; attempt < 50; attempt += 1) {
      if (await this.isHealthy(url)) return;
      await wait(400);
    }
    throw new Error(this.lastError ?? "El frontend local no ha respondido a tiempo.");
  }

  private async isHealthy(url: string): Promise<boolean> {
    try {
      const response = await fetch(url);
      return response.ok;
    } catch {
      return false;
    }
  }

  private log(scope: string, chunk: Buffer): void {
    appendFileSync(
      path.join(getDesktopPaths().logsDir, "desktop-frontend.log"),
      `[${new Date().toISOString()}] [${scope}] ${redactSecrets(chunk.toString())}\n`,
      "utf-8"
    );
  }
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
