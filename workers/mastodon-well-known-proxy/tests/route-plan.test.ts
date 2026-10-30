import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";
import config from "../cloudflare.config";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

function routeMatches(url: URL, route: string): boolean {
  const wildcard = route.endsWith("*");
  const pattern = wildcard ? route.slice(0, -1) : route;
  const slash = pattern.indexOf("/");
  const host = pattern.slice(0, slash);
  const path = pattern.slice(slash);

  return url.hostname === host && (wildcard ? url.pathname.startsWith(path) : url.pathname === path);
}

describe("production route plan", () => {
  it.each([undefined, "production", "development"])(
    "keeps %s route-free with public previews disabled",
    (mode) => {
      const worker = config({ mode, isPreview: false }).worker;
      expect(worker.name).toBe("palewire-mastodon-well-known-proxy");
      expect(worker.workersDev).toBe(false);
      expect(worker.previewUrls).toBe(false);
      expect(worker).not.toHaveProperty("triggers");
      expect(worker).not.toHaveProperty("env");
    },
  );

  it("rejects misspelled modes and implicit Worker Previews", () => {
    expect(() => config({ mode: "prodution", isPreview: false })).toThrow("Unknown Mastodon Worker mode");
    expect(() => config({ mode: "production", isPreview: true })).toThrow("named canary modes");
  });

  it("only attaches the approved routes in the explicit attachment modes", () => {
    const production = config({ mode: "production-routes", isPreview: false }).worker;
    const canary = config({ mode: "same-zone-canary-route", isPreview: false }).worker;

    expect(production.name).toBe("palewire-mastodon-well-known-proxy");
    expect(production.workersDev).toBe(false);
    expect(production.previewUrls).toBe(false);
    expect(production).not.toHaveProperty("env");
    expect(production).toHaveProperty("triggers", [
      { type: "fetch", pattern: "palewi.re/.well-known/webfinger*", zone: "palewi.re" },
      { type: "fetch", pattern: "palewi.re/.well-known/host-meta*", zone: "palewi.re" },
      { type: "fetch", pattern: "palewi.re/.well-known/nodeinfo*", zone: "palewi.re" },
    ]);
    expect(canary.name).toBe("palewire-mastodon-well-known-proxy-same-zone-canary");
    expect(canary).toHaveProperty("triggers", [
      { type: "fetch", pattern: "palewi.re/.well-known/cloudflare-worker-canary", zone: "palewi.re" },
    ]);
  });

  it("compiles the exact production routes without matching the same-zone upstream host", () => {
    const routes = execFileSync("make", ["--no-print-directory", "-s", "worker-route-plan"], {
      cwd: repositoryRoot,
      encoding: "utf8",
    })
      .trim()
      .split(/\s+/)
      .filter((value) => value !== "--route");
    const productionRequests = [
      new URL("https://palewi.re/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re"),
      new URL("https://palewi.re/.well-known/host-meta"),
      new URL("https://palewi.re/.well-known/nodeinfo"),
    ];
    const upstream = new URL("https://mastodon.palewi.re/.well-known/nodeinfo");

    expect(routes).toEqual([
      "palewi.re/.well-known/webfinger*",
      "palewi.re/.well-known/host-meta*",
      "palewi.re/.well-known/nodeinfo*",
    ]);
    for (const request of productionRequests) {
      expect(routes.some((route) => routeMatches(request, route))).toBe(true);
    }
    expect(routes.some((route) => routeMatches(upstream, route))).toBe(false);
  });
});
