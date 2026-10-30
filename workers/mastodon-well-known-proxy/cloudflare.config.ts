import { bindings, defineConfig, triggers } from "cf/config";

export const productionRoutes = [
  "palewi.re/.well-known/webfinger*",
  "palewi.re/.well-known/host-meta*",
  "palewi.re/.well-known/nodeinfo*",
];
export const sameZoneCanaryRoute = "palewi.re/.well-known/cloudflare-worker-canary";
export const startupCanaryName = "palewire-mastodon-well-known-proxy-canary";
export const sameZoneCanaryName = "palewire-mastodon-well-known-proxy-same-zone-canary";
export const productionName = "palewire-mastodon-well-known-proxy";

export default defineConfig(({ mode, isPreview }) => {
  if (isPreview) {
    throw new Error("Use the named canary modes instead of Worker Previews.");
  }
  const worker = {
    name: productionName,
    entrypoint: "src/index.ts",
    compatibilityDate: "2026-08-24",
    compatibilityFlags: ["global_fetch_strictly_public"],
    workersDev: false,
    previewUrls: false,
    observability: { enabled: true, headSamplingRate: 1 },
  };

  switch (mode) {
    case undefined:
    case "production":
      return { worker };
    case "production-routes":
      return {
        worker: {
          ...worker,
          triggers: productionRoutes.map((pattern) => triggers.fetch({ pattern, zone: "palewi.re" })),
        },
      };
    case "startup-canary":
      return {
        worker: { ...worker, name: startupCanaryName, workersDev: true, previewUrls: true },
      };
    case "same-zone-canary":
    case "same-zone-canary-route":
      return {
        worker: {
          ...worker,
          name: sameZoneCanaryName,
          workersDev: true,
          previewUrls: true,
          env: { CANARY_PATH: bindings.text("/.well-known/cloudflare-worker-canary") },
          triggers: mode === "same-zone-canary-route"
            ? [triggers.fetch({ pattern: sameZoneCanaryRoute, zone: "palewi.re" })]
            : [],
        },
      };
    default:
      throw new Error(`Unknown Mastodon Worker mode: ${mode}`);
  }
});
