import { describe, expect, it } from "vitest";

import { routePlan, rules } from "../src/index";

function routeMatches(url: URL, route: string): boolean {
  const [host, ...parts] = route.split("/");
  const expression = `^/${parts.join("/").replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replaceAll("\\*", ".*")}$`;
  return url.hostname === host && new RegExp(expression).test(`${url.pathname}${url.search}`);
}

describe("production route plan", () => {
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
