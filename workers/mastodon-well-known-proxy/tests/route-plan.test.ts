import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

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
