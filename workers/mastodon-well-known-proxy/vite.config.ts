import { cloudflare } from "@cloudflare/vite-plugin";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [cloudflare({ inspectorPort: false })],
  server: {
    host: "127.0.0.1",
    port: process.env.MASTODON_DEV_PORT ? Number(process.env.MASTODON_DEV_PORT) : 5173,
    strictPort: true,
  },
});
