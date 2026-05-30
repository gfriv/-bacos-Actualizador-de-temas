import { CHANNELS, type DesktopChannel } from "../ipc/channels";

const ALLOWED_CHANNELS = new Set<string>(Object.values(CHANNELS));

export function assertAllowedChannel(channel: string): asserts channel is DesktopChannel {
  if (!ALLOWED_CHANNELS.has(channel)) {
    throw new Error("Canal IPC no permitido.");
  }
}

export function assertSafeModelName(modelName: string): void {
  if (!/^[A-Za-z0-9._:/-]{1,96}$/.test(modelName)) {
    throw new Error("Nombre de modelo no valido.");
  }
}

export function assertSafeSecretKey(key: string): void {
  if (!/^[A-Za-z0-9._:-]{1,80}$/.test(key)) {
    throw new Error("Identificador de secreto no valido.");
  }
}
