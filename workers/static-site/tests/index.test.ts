import { describe, expect, it } from "vitest";

import { handleRequest, type StaticAssets } from "../src/index";

const assets: StaticAssets = {
  async fetch(request) {
    return new Response(request.url, {
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  },
};

function request(path: string, hostname = "palewi.re"): Request {
  return new Request(`https://${hostname}${path}`);
}

describe("static site Worker", () => {
  it("preserves the site's HTTP redirects", async () => {
    await expect(handleRequest(request("/"), { ASSETS: assets })).resolves.toMatchObject({
      status: 302,
      headers: expect.any(Headers),
    });
    const root = await handleRequest(request("/"), { ASSETS: assets });
    const favicon = await handleRequest(request("/favicon.ico"), { ASSETS: assets });
    const username = await handleRequest(request("/@palewire"), { ASSETS: assets });

    expect(root.headers.get("location")).toBe("/who-is-ben-welsh/");
    expect(favicon.headers.get("location")).toBe("/static/favicon.ico");
    expect(username.headers.get("location")).toBe("https://mastodon.palewi.re/@palewire");
  });

  it("redirects sibling domains to the canonical host", async () => {
    const hosts = ["www.palewi.re", "palewire.com", "www.palewire.com"];

    for (const host of hosts) {
      const response = await handleRequest(request("/posts/?source=test", host), { ASSETS: assets });

      expect(response.status).toBe(301);
      expect(response.headers.get("location")).toBe("https://palewi.re/posts/?source=test");
    }
  });

  it("keeps the health check available without fetching an asset", async () => {
    const response = await handleRequest(request("/health/"), { ASSETS: assets });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ status: "ok" });
  });

  it("serves the RSS file with its XML content type", async () => {
    const response = await handleRequest(request("/feeds/posts/"), { ASSETS: assets });

    expect(response.headers.get("content-type")).toBe("application/rss+xml; charset=utf-8");
    await expect(response.text()).resolves.toContain("/feeds/posts/index.xml");
  });

  it("passes static assets through with security headers", async () => {
    const response = await handleRequest(request("/who-is-ben-welsh/"), { ASSETS: assets });

    expect(await response.text()).toBe("https://palewi.re/who-is-ben-welsh/");
    expect(response.headers.get("content-security-policy")).toBe(
      "base-uri 'self'; default-src 'self'; form-action 'self'; frame-ancestors 'none'; frame-src 'self' https://docs.google.com https://player.vimeo.com http://s3-us-west-1.amazonaws.com https://w.soundcloud.com; img-src 'self' https://palewi.re http://chart.apis.google.com http://www.palewire.com; font-src 'self' https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self'; media-src 'self'; object-src 'none'",
    );
    expect(response.headers.get("permissions-policy")).toBe(
      "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
    );
    expect(response.headers.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    expect(response.headers.get("strict-transport-security")).toContain("max-age=31536000");
  });

  it("applies the security policy to redirects and health responses", async () => {
    const redirectResponse = await handleRequest(request("/"), { ASSETS: assets });
    const healthResponse = await handleRequest(request("/health/"), { ASSETS: assets });

    for (const response of [redirectResponse, healthResponse]) {
      expect(response.headers.get("content-security-policy")).toContain("frame-ancestors 'none'");
      expect(response.headers.get("permissions-policy")).toBe(
        "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
      );
    }
  });
});
