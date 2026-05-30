import { cp, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const webDir = path.join(root, "apps", "web");
const sourceStandalone = path.join(webDir, ".next", "standalone");
const targetStandalone = path.join(webDir, ".next", "standalone-electron");
const sourceStatic = path.join(webDir, ".next", "static");
const targetStatic = path.join(targetStandalone, "apps", "web", ".next", "static");
const sourcePublic = path.join(webDir, "public");
const targetPublic = path.join(targetStandalone, "apps", "web", "public");

if (!existsSync(sourceStandalone)) {
  throw new Error("No existe apps/web/.next/standalone. Ejecuta primero el build de Next con DESKTOP_BUILD=1.");
}

await rm(targetStandalone, { recursive: true, force: true });
await cp(sourceStandalone, targetStandalone, {
  recursive: true,
  dereference: true,
  force: true
});

if (existsSync(sourceStatic)) {
  await cp(sourceStatic, targetStatic, {
    recursive: true,
    dereference: true,
    force: true
  });
}

if (existsSync(sourcePublic)) {
  await cp(sourcePublic, targetPublic, {
    recursive: true,
    dereference: true,
    force: true
  });
}

console.log("Standalone de Electron preparado sin symlinks de pnpm.");
