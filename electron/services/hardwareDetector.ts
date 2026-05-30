import os from "node:os";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { statfs } from "node:fs/promises";
import { getDesktopPaths } from "./appPaths";
import type { HardwareProfile } from "../types/desktop";

const execFileAsync = promisify(execFile);

export async function detectHardware(): Promise<HardwareProfile> {
  const platform = os.platform();
  const profile: HardwareProfile = {
    os: platform === "win32" ? "windows" : platform === "darwin" ? "macos" : platform === "linux" ? "linux" : "unknown",
    arch: os.arch() === "x64" ? "x64" : os.arch() === "arm64" ? "arm64" : "unknown",
    totalRamGB: bytesToGB(os.totalmem()),
    freeRamGB: bytesToGB(os.freemem()),
    cpuModel: os.cpus()[0]?.model,
    cpuCores: os.cpus().length,
    gpuVendor: platform === "darwin" && os.arch() === "arm64" ? "apple" : "unknown",
    hasAppleSilicon: platform === "darwin" && os.arch() === "arm64"
  };

  const diskFreeGB = await detectDiskFreeGB();
  if (diskFreeGB !== undefined) profile.diskFreeGB = diskFreeGB;

  if (platform === "win32") {
    Object.assign(profile, await detectWindowsGpu());
  } else if (platform === "linux" || platform === "darwin") {
    Object.assign(profile, await detectNvidia());
  }

  return profile;
}

async function detectDiskFreeGB(): Promise<number | undefined> {
  try {
    const stats = await statfs(getDesktopPaths().dataDir);
    return bytesToGB(stats.bavail * stats.bsize);
  } catch {
    return undefined;
  }
}

async function detectWindowsGpu(): Promise<Partial<HardwareProfile>> {
  try {
    const { stdout } = await execFileAsync("powershell", [
      "-NoProfile",
      "-Command",
      "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name,AdapterRAM | ConvertTo-Json -Compress"
    ]);
    const parsed = JSON.parse(stdout || "{}") as { Name?: string; AdapterRAM?: number };
    const name = parsed.Name ?? "";
    const lowered = name.toLowerCase();
    return {
      gpuModel: name || undefined,
      gpuVendor: lowered.includes("nvidia")
        ? "nvidia"
        : lowered.includes("amd") || lowered.includes("radeon")
          ? "amd"
          : lowered.includes("intel")
            ? "intel"
            : "unknown",
      gpuMemoryGB: parsed.AdapterRAM ? bytesToGB(parsed.AdapterRAM) : undefined,
      hasNvidiaCuda: lowered.includes("nvidia")
    };
  } catch {
    return await detectNvidia();
  }
}

async function detectNvidia(): Promise<Partial<HardwareProfile>> {
  try {
    const { stdout } = await execFileAsync("nvidia-smi", [
      "--query-gpu=name,memory.total",
      "--format=csv,noheader,nounits"
    ]);
    const [name, memory] = stdout.split(/\r?\n/)[0]?.split(",").map((value) => value.trim()) ?? [];
    return {
      gpuVendor: "nvidia",
      gpuModel: name,
      gpuMemoryGB: memory ? Math.round(Number(memory) / 1024) : undefined,
      hasNvidiaCuda: true
    };
  } catch {
    return { gpuVendor: "none", hasNvidiaCuda: false };
  }
}

function bytesToGB(value: number): number {
  return Math.round((value / 1024 ** 3) * 10) / 10;
}
