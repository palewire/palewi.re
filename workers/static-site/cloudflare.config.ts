import { bindings, defineConfig, triggers } from "cf/config";

export default defineConfig(({ mode, isPreview }) => {
  if (isPreview) {
    throw new Error("Use the named static-site preview mode instead of Worker Previews.");
  }
  const worker = {
    name: "palewire-static-site",
    entrypoint: "src/index.ts",
    compatibilityDate: "2026-08-25",
    workersDev: false,
    previewUrls: false,
    observability: { enabled: true, headSamplingRate: 1 },
    assets: {
      htmlHandling: "auto-trailing-slash" as const,
      notFoundHandling: "404-page" as const,
      runWorkerFirst: true,
    },
    env: {
      TALK_MEDIA: bindings.r2({ name: "palewire-talk-media", dev: { remote: true } }),
      ASSETS: bindings.assets(),
    },
  };
  switch (mode) {
    case undefined:
    case "production":
      return {
        worker: {
          ...worker,
          triggers: [
            triggers.fetch({ pattern: "palewi.re/*", zone: "palewi.re" }),
            triggers.fetch({ pattern: "www.palewi.re/*", zone: "palewi.re" }),
            triggers.fetch({ pattern: "palewire.com/*", zone: "palewire.com" }),
            triggers.fetch({ pattern: "www.palewire.com/*", zone: "palewire.com" }),
          ],
        },
      };
    case "development":
      return {
        worker: {
          ...worker,
          name: "palewire-static-site-development",
          triggers: [],
        },
      };
    case "preview":
      return {
        worker: {
          ...worker,
          name: "palewire-static-site-preview",
          workersDev: true,
          previewUrls: true,
          triggers: [],
        },
      };
    default:
      throw new Error(`Unknown static-site Worker mode: ${mode}`);
  }
});
