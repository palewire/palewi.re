import { execFileSync } from "node:child_process";
import { fileURLToPath, URL } from "node:url";
import { bindings, defineConfig, triggers } from "cf/config";

const repositoryRoot = fileURLToPath(new URL("../../", import.meta.url));

export function productionRoutePlan(): string[] {
  const output = execFileSync("uv", [
    "run", "--locked", "python", "-c",
    "import json; from project.redirect_manifest import RULES, cloudflare_route_plan; print(json.dumps(cloudflare_route_plan(RULES)))",
  ], {
    cwd: repositoryRoot,
    env: { ...process.env, UV_NO_ENV_FILE: "1" },
    encoding: "utf8",
  });
  const routes: unknown = JSON.parse(output);
  if (!Array.isArray(routes) || routes.length === 0
    || !routes.every((route): route is string => typeof route === "string")) {
    throw new Error("The Python redirect validator returned an invalid route plan.");
  }
  return routes;
}

export default defineConfig(({ mode, isPreview }) => {
  if (isPreview) {
    throw new Error("Use the named legacy canary modes instead of Worker Previews.");
  }
  const worker = {
    name: "palewire-legacy-redirects",
    entrypoint: "src/index.ts",
    compatibilityDate: "2026-08-24",
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
          triggers: productionRoutePlan().map((pattern) => triggers.fetch({ pattern, zone: "palewi.re" })),
        },
      };
    case "startup-canary":
      return {
        worker: { ...worker, name: "palewire-legacy-redirects-canary", workersDev: true, previewUrls: true },
      };
    case "same-zone-canary":
    case "same-zone-canary-route":
      return {
        worker: {
          ...worker,
          name: "palewire-legacy-redirects-same-zone-canary",
          workersDev: true,
          previewUrls: true,
          env: { CANARY_PATH: bindings.text("/legacy-redirects-canary") },
          triggers: mode === "same-zone-canary-route"
            ? [triggers.fetch({ pattern: "palewi.re/legacy-redirects-canary*", zone: "palewi.re" })]
            : [],
        },
      };
    default:
      throw new Error(`Unknown legacy Worker mode: ${mode}`);
  }
});
