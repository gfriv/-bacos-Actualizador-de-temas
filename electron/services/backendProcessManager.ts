import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import path from "node:path";
import { appendFileSync } from "node:fs";
import { getDesktopPaths, getRepoRoot } from "./appPaths";
import { redactSecrets } from "../security/secretRedaction";
import type { BackendStatus } from "../types/desktop";

const BACKEND_HOST = "127.0.0.1";
const BACKEND_PORT = 8765;
const BACKEND_BASE_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}/api`;

export class BackendProcessManager {
  private process: ChildProcessWithoutNullStreams | null = null;
  private lastError: string | undefined;

  constructor(private readonly rendererUrl = process.env.ABACOS_RENDERER_URL ?? "http://127.0.0.1:3000") {}

  get baseUrl(): string {
    return BACKEND_BASE_URL;
  }

  async start(): Promise<BackendStatus> {
    if (await this.isHealthy()) {
      return this.status();
    }
    if (this.process && !this.process.killed) {
      return this.waitUntilHealthy();
    }

    const root = getRepoRoot();
    const apiDir = path.join(root, "apps", "api");
    const desktopPaths = getDesktopPaths();
    const env = {
      ...process.env,
      DATABASE_URL: desktopPaths.apiDatabaseUrl,
      STORAGE_BACKEND: "local",
      UPLOAD_DIR: desktopPaths.uploadDir,
      GENERATED_DIR: desktopPaths.generatedDir,
      CORS_ORIGINS: JSON.stringify([this.rendererUrl, `http://${BACKEND_HOST}:${BACKEND_PORT}`]),
      DEMO_ACCESS_ENABLED: "true",
      OCR_ENABLED: "false",
      PYTHONUTF8: "1"
    };

    await this.runCommand("python", ["-m", "uv", "run", "alembic", "upgrade", "head"], apiDir, env);
    this.process = spawn(
      "python",
      [
        "-m",
        "uv",
        "run",
        "uvicorn",
        "app.main:app",
        "--host",
        BACKEND_HOST,
        "--port",
        String(BACKEND_PORT)
      ],
      { cwd: apiDir, env, windowsHide: true, stdio: "pipe" }
    );
    this.process.stdout.on("data", (chunk) => this.log("api", chunk));
    this.process.stderr.on("data", (chunk) => this.log("api", chunk));
    this.process.once("exit", (code) => {
      this.lastError = code === 0 ? undefined : `Backend finalizado con codigo ${code ?? "desconocido"}.`;
      this.process = null;
    });

    return this.waitUntilHealthy();
  }

  async restart(): Promise<BackendStatus> {
    await this.stop();
    return this.start();
  }

  async stop(): Promise<void> {
    if (this.process && !this.process.killed) {
      this.process.kill();
      await wait(1200);
    }
    this.process = null;
  }

  async status(): Promise<BackendStatus> {
    return {
      running: await this.isHealthy(),
      baseUrl: BACKEND_BASE_URL,
      pid: this.process?.pid,
      error: this.lastError
    };
  }

  private async waitUntilHealthy(): Promise<BackendStatus> {
    for (let attempt = 0; attempt < 40; attempt += 1) {
      if (await this.isHealthy()) return this.status();
      await wait(500);
    }
    this.lastError = "El backend local no ha respondido a tiempo.";
    return this.status();
  }

  private async isHealthy(): Promise<boolean> {
    try {
      const response = await fetch(`${BACKEND_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  private async runCommand(
    command: string,
    args: string[],
    cwd: string,
    env: NodeJS.ProcessEnv
  ): Promise<void> {
    await new Promise<void>((resolve, reject) => {
      const child = spawn(command, args, { cwd, env, windowsHide: true, stdio: "pipe" });
      child.stdout.on("data", (chunk) => this.log("migration", chunk));
      child.stderr.on("data", (chunk) => this.log("migration", chunk));
      child.once("exit", (code) => {
        if (code === 0) resolve();
        else reject(new Error("No se pudieron aplicar las migraciones locales."));
      });
    });
  }

  private log(scope: string, chunk: Buffer): void {
    const logsDir = getDesktopPaths().logsDir;
    appendFileSync(
      path.join(logsDir, "desktop-backend.log"),
      `[${new Date().toISOString()}] [${scope}] ${redactSecrets(chunk.toString())}\n`,
      "utf-8"
    );
  }
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
