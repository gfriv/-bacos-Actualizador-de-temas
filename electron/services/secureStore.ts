import { safeStorage } from "electron";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { getDesktopPaths } from "./appPaths";
import { assertSafeSecretKey } from "../security/ipcGuards";

type SecretFile = Record<string, string>;

export class SecureSecretsStore {
  private readonly filePath = path.join(getDesktopPaths().configDir, "secrets.enc.json");

  setSecret(key: string, value: string): void {
    assertSafeSecretKey(key);
    if (!safeStorage.isEncryptionAvailable()) {
      throw new Error("El almacenamiento seguro del sistema no esta disponible.");
    }
    const secrets = this.readSecrets();
    secrets[key] = safeStorage.encryptString(value).toString("base64");
    this.writeSecrets(secrets);
  }

  getSecret(key: string): string | null {
    assertSafeSecretKey(key);
    if (!safeStorage.isEncryptionAvailable()) return null;
    const encrypted = this.readSecrets()[key];
    if (!encrypted) return null;
    return safeStorage.decryptString(Buffer.from(encrypted, "base64"));
  }

  deleteSecret(key: string): void {
    assertSafeSecretKey(key);
    const secrets = this.readSecrets();
    delete secrets[key];
    this.writeSecrets(secrets);
  }

  private readSecrets(): SecretFile {
    if (!existsSync(this.filePath)) return {};
    try {
      return JSON.parse(readFileSync(this.filePath, "utf-8")) as SecretFile;
    } catch {
      return {};
    }
  }

  private writeSecrets(secrets: SecretFile): void {
    writeFileSync(this.filePath, JSON.stringify(secrets, null, 2), "utf-8");
  }
}
