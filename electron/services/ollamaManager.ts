import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { once } from "node:events";
import { assertSafeModelName } from "../security/ipcGuards";
import type { OllamaModelInfo, OllamaPullProgress, OllamaStatus } from "../types/desktop";

const DEFAULT_BASE_URL = "http://127.0.0.1:11434";

export class OllamaManager {
  private process: ChildProcessWithoutNullStreams | null = null;

  constructor(private readonly baseUrl = DEFAULT_BASE_URL) {}

  async detectOllama(): Promise<OllamaStatus> {
    const installed = await this.isInstalled();
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return { installed, running: true, baseUrl: this.baseUrl };
    } catch (error) {
      return {
        installed,
        running: false,
        baseUrl: this.baseUrl,
        error: error instanceof Error ? error.message : "Ollama no responde."
      };
    }
  }

  async startOllama(): Promise<OllamaStatus> {
    const status = await this.detectOllama();
    if (status.running) return status;
    if (!status.installed) {
      return { ...status, error: "Ollama no está instalado o no está en PATH." };
    }
    this.process = spawn("ollama", ["serve"], {
      windowsHide: true,
      stdio: "pipe",
      env: { ...process.env, OLLAMA_HOST: "127.0.0.1:11434" }
    });
    this.process.once("exit", () => {
      this.process = null;
    });
    await wait(1500);
    return this.detectOllama();
  }

  async stopOllama(): Promise<void> {
    if (this.process && !this.process.killed) {
      this.process.kill();
      await Promise.race([once(this.process, "exit"), wait(2000)]);
    }
    this.process = null;
  }

  async restartOllama(): Promise<OllamaStatus> {
    await this.stopOllama();
    return this.startOllama();
  }

  async listLocalModels(): Promise<OllamaModelInfo[]> {
    const response = await fetch(`${this.baseUrl}/api/tags`);
    if (!response.ok) throw new Error("No se pudieron listar modelos de Ollama.");
    const data = (await response.json()) as { models?: Array<Record<string, unknown>> };
    return (data.models ?? []).map((item) => ({
      name: String(item.name ?? ""),
      size: typeof item.size === "number" ? item.size : undefined,
      modifiedAt: typeof item.modified_at === "string" ? item.modified_at : undefined,
      family: readDetails(item, "family"),
      parameterSize: readDetails(item, "parameter_size"),
      quantization: readDetails(item, "quantization_level")
    })).filter((item) => item.name);
  }

  async pullModel(
    modelName: string,
    onProgress?: (progress: OllamaPullProgress) => void
  ): Promise<void> {
    assertSafeModelName(modelName);
    const response = await fetch(`${this.baseUrl}/api/pull`, {
      method: "POST",
      body: JSON.stringify({ name: modelName, stream: true })
    });
    if (!response.ok || !response.body) throw new Error("No se pudo iniciar la descarga del modelo.");

    const decoder = new TextDecoder();
    let buffer = "";
    for await (const chunk of response.body as unknown as AsyncIterable<Uint8Array>) {
      buffer += decoder.decode(chunk, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.trim()) continue;
        const progress = JSON.parse(line) as OllamaPullProgress;
        if (progress.total && progress.completed) {
          progress.percent = Math.round((progress.completed / progress.total) * 100);
        }
        onProgress?.(progress);
      }
    }
  }

  async deleteModel(modelName: string): Promise<void> {
    assertSafeModelName(modelName);
    const response = await fetch(`${this.baseUrl}/api/delete`, {
      method: "DELETE",
      body: JSON.stringify({ name: modelName })
    });
    if (!response.ok) throw new Error("No se pudo eliminar el modelo.");
  }

  async testModel(modelName: string): Promise<boolean> {
    assertSafeModelName(modelName);
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: "POST",
      body: JSON.stringify({
        model: modelName,
        prompt: "Responde solo con OK.",
        stream: false,
        options: { num_predict: 8, temperature: 0 }
      })
    });
    return response.ok;
  }

  async warmupModel(modelName: string): Promise<void> {
    await this.testModel(modelName);
  }

  private async isInstalled(): Promise<boolean> {
    const child = spawn("ollama", ["--version"], { windowsHide: true, stdio: "ignore" });
    const [code] = (await once(child, "exit")) as [number | null];
    return code === 0;
  }
}

function readDetails(item: Record<string, unknown>, key: string): string | undefined {
  const details = item.details;
  if (!details || typeof details !== "object") return undefined;
  const value = (details as Record<string, unknown>)[key];
  return typeof value === "string" ? value : undefined;
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
