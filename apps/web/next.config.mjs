import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const turbopackRoot = process.env.VERCEL ? __dirname : path.resolve(__dirname, "../..");

/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  turbopack: {
    root: turbopackRoot,
  },
};

export default nextConfig;
