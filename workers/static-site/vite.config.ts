import { existsSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";

import { cloudflare } from "@cloudflare/vite-plugin";
import { defineConfig } from "vite";

const assetDirectory = fileURLToPath(new URL("../../dist", import.meta.url));

export default defineConfig(({ command }) => {
  if (command === "build" && !existsSync(`${assetDirectory}/who-is-ben-welsh/index.html`)) {
    throw new Error("Run make bake before building the static-site Worker.");
  }
  return {
    publicDir: assetDirectory,
    plugins: [cloudflare({
      inspectorPort: false,
      remoteBindings: process.env.STATIC_WORKER_LOCAL !== "1",
    })],
    server: {
      host: "127.0.0.1",
      port: process.env.STATIC_DEV_PORT ? Number(process.env.STATIC_DEV_PORT) : 5173,
      strictPort: true,
    },
  };
});
