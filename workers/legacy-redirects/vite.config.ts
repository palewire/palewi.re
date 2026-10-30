import { fileURLToPath, URL } from "node:url";

import { cloudflare } from "@cloudflare/vite-plugin";
import { defineConfig } from "vite";

const manifestPath = fileURLToPath(new URL("../../project/redirects.yaml", import.meta.url));

export default defineConfig({
  plugins: [cloudflare({ inspectorPort: false })],
  server: {
    host: "127.0.0.1",
    port: process.env.LEGACY_DEV_PORT ? Number(process.env.LEGACY_DEV_PORT) : 5173,
    strictPort: true,
    fs: {
      allow: [
        fileURLToPath(new URL(".", import.meta.url)),
        // Vite checks both the file path and its raw import ID.
        manifestPath,
        `${manifestPath}?raw`,
      ],
    },
  },
});
