import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";
import { parse } from "yaml";

import { handleRequest, loadManifest, routePlan, rules } from "../src/index";

const BASE_URL = "https://palewi.re";
const MARKER = "cloudflare-worker-v1";

interface ManifestRecord {
  source: string;
  destination: string;
  examples?: string[];
}

function request(path: string, init?: RequestInit): Request {
  return new Request(`${BASE_URL}${path}`, init);
}

function expectedDestination(record: ManifestRecord, path: string): string {
  const rule = rules.find((candidate) => candidate.source === record.source);
  if (rule === undefined) {
    throw new Error(`Missing rule for ${record.source}`);
  }
  const match = rule.matcher.exec(path);
  if (match === null) {
    throw new Error(`Manifest example ${path} did not match ${record.source}`);
  }
  return record.destination.replace(/\{([a-z][a-z0-9_]*)\}/g, (_template, name: string) => match.groups?.[name] ?? "");
}

describe("legacy redirect Worker", () => {
  const manifest = parse(readFileSync(new URL("../../../project/redirects.yaml", import.meta.url), "utf8")) as {
    redirects: ManifestRecord[];
  };

  it("disables public production exposure and keeps explicit canaries available", () => {
    const config = JSON.parse(readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8"));

    expect(config.workers_dev).toBe(false);
    expect(config.preview_urls).toBe(false);
    expect(config.routes).toBeUndefined();
    expect(config.route).toBeUndefined();
    expect(config.compatibility_flags ?? []).not.toContain("global_fetch_strictly_public");
    expect(config.env["startup-canary"]).toEqual({
      name: "palewire-legacy-redirects-startup-canary",
      workers_dev: true,
      preview_urls: true,
    });
    expect(config.env["same-zone-canary"].workers_dev).toBe(true);
    expect(config.env["same-zone-canary"].preview_urls).toBe(true);
    expect(config.env["same-zone-canary"].vars).toEqual({ CANARY_PATH: "/legacy-redirects-canary" });
  });

  it("has 21 exact and 8 dynamic rules with a unique narrow Cloudflare route plan", () => {
    const exact = manifest.redirects.filter((rule) => rule.examples === undefined);
    const dynamic = manifest.redirects.filter((rule) => rule.examples !== undefined);

    expect(exact).toHaveLength(21);
    expect(dynamic).toHaveLength(8);
    expect(routePlan).toHaveLength(36);
    expect(routePlan.every((route) => route.startsWith("palewi.re/"))).toBe(true);
    expect(routePlan.some((route) => route === "palewi.re/*")).toBe(false);
    expect(routePlan.every((route) => route.endsWith("*") && !route.slice(0, -1).includes("*"))).toBe(true);
  });

  it("matches every static redirect, drops query strings, and preserves its 302 destination", () => {
    for (const record of manifest.redirects.filter((rule) => rule.examples === undefined)) {
      const response = handleRequest(request(`/${record.source}?source=test`));

      expect(response.status, record.source).toBe(302);
      expect(response.headers.get("location"), record.source).toBe(record.destination);
      expect(response.headers.get("x-palewire-legacy-redirect"), record.source).toBe(MARKER);
    }
  });

  it("matches representative and boundary cases for every dynamic redirect", () => {
    for (const record of manifest.redirects.filter((rule) => rule.examples !== undefined)) {
      for (const example of record.examples ?? []) {
        const response = handleRequest(request(`${example}?source=test`));

        expect(response.status, example).toBe(302);
        expect(response.headers.get("location"), example).toBe(expectedDestination(record, example));
        expect(response.headers.get("x-palewire-legacy-redirect"), example).toBe(MARKER);
      }
    }
  });

  it("does not redirect route overmatches, adjacent current paths, or unsupported methods", () => {
    for (const path of [
      "/1/02/03/post/",
      "/2024/2/03/post/",
      "/2024/02/3/post/",
      "/apps/page/not-a-number/",
      "/posts/2026/08/24/current-post/",
      "/who-is-ben-welsh/",
    ]) {
      const response = handleRequest(request(path));
      expect(response.status, path).toBe(404);
      expect(response.headers.get("location"), path).toBeNull();
      expect(response.headers.get("x-palewire-legacy-redirect"), path).toBeNull();
    }
    const response = handleRequest(request("/feed/", { method: "POST" }));
    expect(response.status).toBe(405);
    expect(response.headers.get("allow")).toBe("GET, HEAD");
  });

  it("hands current app destinations back to the static site", () => {
    const first = handleRequest(request("/applications/"));
    const second = handleRequest(request(first.headers.get("location") ?? ""));

    expect(first.headers.get("location")).toBe("/apps/");
    expect(second.status).toBe(404);
    expect(second.headers.get("location")).toBeNull();
  });

  it("rejects malformed, unsafe, overlapping, and looping manifest records", () => {
    expect(() => loadManifest("redirects:\n  - source: feed/\n    destination: javascript:alert(1)\n")).toThrow("HTTP(S)");
    expect(() => loadManifest("redirects:\n  - source: feed/\n    destination: /\n  - source: feed/\n    destination: /work/\n")).toThrow("overlaps");
    expect(() => loadManifest("redirects:\n  - source: tag/{tag}/\n    destination: /{missing}/\n    captures: {tag: segment}\n    examples: [/tag/a/]\n")).toThrow("unknown capture");
    expect(() => loadManifest("redirects:\n  - source: ../feed/\n    destination: /\n")).toThrow("unsafe");
    expect(() => loadManifest("redirects:\n  - source: feed/*\n    destination: /\n")).toThrow("relative path");
    expect(() => loadManifest("redirects:\n  - source: loop/\n    destination: /loop/\n")).toThrow("loops");
    expect(() => loadManifest("redirects:\n  - source: apps/page/{page}/\n    destination: /apps/page/{page}/\n    captures: {page: digits}\n    routes: [apps/page/]\n    examples: [/apps/page/1/]\n")).toThrow("loops");
  });

  it("serves the canary only when that named environment enables it", () => {
    expect(handleRequest(request("/legacy-redirects-canary")).status).toBe(404);
    const response = handleRequest(request("/legacy-redirects-canary"), { CANARY_PATH: "/legacy-redirects-canary" });
    expect(response.status).toBe(204);
    expect(response.headers.get("x-palewire-legacy-redirect")).toBe(MARKER);
  });
});
