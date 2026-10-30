import { describe, expect, it } from "vitest";

import { routePlan, rules } from "../src/index";
import config, { productionRoutePlan } from "../cloudflare.config";

function routeMatches(url: URL, route: string): boolean {
  const [host, ...parts] = route.split("/");
  const expression = `^/${parts.join("/").replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replaceAll("\\*", ".*")}$`;
  return url.hostname === host && new RegExp(expression).test(`${url.pathname}${url.search}`);
}

describe("production route plan", () => {
  it.each([
    [undefined, "palewire-legacy-redirects"],
    ["production", "palewire-legacy-redirects"],
    ["development", "palewire-legacy-redirects-development"],
  ])(
    "keeps %s route-free with public previews disabled",
    (mode, name) => {
      const worker = config({ mode, isPreview: false }).worker;
      expect(worker.name).toBe(name);
      expect(worker.workersDev).toBe(false);
      expect(worker.previewUrls).toBe(false);
      expect(worker).not.toHaveProperty("triggers");
      expect(worker).not.toHaveProperty("env");
    },
  );

  it("deploys the Python route plan and keeps the same-zone canary on its own path", () => {
    const pythonRoutes = productionRoutePlan();
    const production = config({ mode: "production-routes", isPreview: false }).worker;
    const canary = config({ mode: "same-zone-canary-route", isPreview: false }).worker;
    expect(pythonRoutes).toEqual(routePlan);
    expect(production).toHaveProperty("triggers", pythonRoutes.map((pattern) => ({ type: "fetch", pattern, zone: "palewi.re" })));
    expect(production.name).toBe("palewire-legacy-redirects");
    expect(production.workersDev).toBe(false);
    expect(production.previewUrls).toBe(false);
    expect(production).not.toHaveProperty("env");
    expect(canary.name).toBe("palewire-legacy-redirects-same-zone-canary");
    expect(canary).toHaveProperty("triggers", [
      { type: "fetch", pattern: "palewi.re/legacy-redirects-canary*", zone: "palewi.re" },
    ]);
  });

  it("covers every manifest case without a broad route or a same-zone upstream", () => {
    const productionCases = [
      ...rules.filter((rule) => !rule.captures || Object.keys(rule.captures).length === 0).map((rule) => `/${rule.source}`),
      ...rules.flatMap((rule) => rule.examples),
    ];
    const routes = routePlan;

    expect(routes).toHaveLength(36);
    expect(new Set(routes)).toHaveLength(36);
    expect(routes).not.toContain("palewi.re/*");
    expect(routes.every((route) => route.endsWith("*") && !route.slice(0, -1).includes("*"))).toBe(true);
    for (const path of productionCases) {
      expect(routes.some((route) => routeMatches(new URL(`https://palewi.re${path}?source=test`), route)), path).toBe(true);
    }
    expect(routes.some((route) => routeMatches(new URL("https://mastodon.palewi.re/feed/"), route))).toBe(false);
    for (const path of [
      "/who-is-ben-welsh/",
      "/apps/",
      "/clips/",
      "/code/",
      "/guides/",
      "/talks/",
      "/docs/",
      "/bots/",
      "/posts/2026/08/24/current-post/",
    ]) {
      expect(routes.some((route) => routeMatches(new URL(`https://palewi.re${path}`), route)), path).toBe(false);
    }
  });
});
