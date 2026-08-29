import { describe, expect, it } from "vitest";

import { handleRequest, type StaticAssets } from "../src/index";

const SECURITY_TXT_CONTENT = [
  "Contact: mailto:b@palewi.re",
  "Expires: 2027-08-01T00:00:00.000Z",
  "Preferred-Languages: en",
  "Canonical: https://palewi.re/.well-known/security.txt",
  "",
].join("\n");

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

  it("serves the JSON Feed with its feed content type and security headers", async () => {
    const content = '{"version":"https://jsonfeed.org/version/1.1"}';
    const response = await handleRequest(request("/feeds/posts.json"), {
      ASSETS: {
        async fetch(assetRequest) {
          expect(new URL(assetRequest.url).pathname).toBe("/feeds/posts.json");
          return new Response(content, {
            headers: { "content-type": "application/json; charset=utf-8" },
          });
        },
      },
    });

    expect(response.headers.get("content-type")).toBe("application/feed+json; charset=utf-8");
    expect(response.headers.get("content-security-policy")).toContain("frame-ancestors 'self'");
    await expect(response.text()).resolves.toBe(content);
  });

  it("serves security.txt directly as plain text", async () => {
    const response = await handleRequest(request("/.well-known/security.txt"), {
      ASSETS: {
        async fetch(assetRequest) {
          expect(new URL(assetRequest.url).pathname).toBe("/.well-known/security.txt");
          return new Response(SECURITY_TXT_CONTENT, {
            headers: { "content-type": "text/html; charset=utf-8" },
          });
        },
      },
    });

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("text/plain; charset=utf-8");
    expect(response.headers.get("location")).toBeNull();
    await expect(response.text()).resolves.toBe(SECURITY_TXT_CONTENT);
  });

  it("serves approved talk media from R2 with byte-range support", async () => {
    const response = await handleRequest(new Request("https://palewi.re/media/talks/a-talk/video.mp4", { headers: { range: "bytes=0-99" } }), {
      ASSETS: assets,
      TALK_MEDIA: {
        async get(key, options) {
          expect(key).toBe("talks/a-talk/video.mp4");
          expect(options?.range).toBeInstanceOf(Headers);
          if (!options?.range) {
            throw new Error("Expected range headers");
          }
          expect(options?.range.get("range")).toBe("bytes=0-99");
          return {
            body: new ReadableStream(),
            httpEtag: '"video"',
            range: { length: 100, offset: 0 },
            size: 1_000,
            writeHttpMetadata(headers) {
              headers.set("content-type", "video/mp4");
            },
          };
        },
        async head() {
          return null;
        },
      },
    });

    expect(response.status).toBe(206);
    expect(response.headers.get("content-range")).toBe("bytes 0-99/1000");
    expect(response.headers.get("content-type")).toBe("video/mp4");
    expect(response.headers.get("cache-control")).toBe("public, max-age=31536000, immutable");
  });

  it("passes static assets through with security headers", async () => {
    const response = await handleRequest(request("/who-is-ben-welsh/"), { ASSETS: assets });

    expect(await response.text()).toBe("https://palewi.re/who-is-ben-welsh/");
    expect(response.headers.get("content-security-policy")).toBe(
      "base-uri 'self'; default-src 'self'; form-action 'self'; frame-ancestors 'self'; frame-src 'self' https://datawrapper.dwcdn.net https://docs.google.com https://player.vimeo.com https://s3-us-west-1.amazonaws.com https://w.soundcloud.com; img-src 'self' https://palewi.re https://palewire.s3.amazonaws.com; font-src 'self' https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self'; media-src 'self' https://palewire.s3.amazonaws.com; object-src 'none'",
    );
    expect(response.headers.get("permissions-policy")).toBe(
      "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
    );
    expect(response.headers.get("referrer-policy")).toBe("strict-origin-when-cross-origin");
    expect(response.headers.get("strict-transport-security")).toContain("max-age=31536000");
  });

  it("allows the IRE Resource Center deck's hashed startup script", async () => {
    const response = await handleRequest(request("/static/talks/ire-resource-center/"), { ASSETS: assets });

    expect(response.headers.get("content-security-policy")).toContain(
      "script-src 'self' 'sha256-DMbYlXrnLW14j2GxDuz+ZgtHhA88TY8qe5iEQIAvWbc='",
    );
  });

  it("applies the security policy to redirects and health responses", async () => {
    const redirectResponse = await handleRequest(request("/"), { ASSETS: assets });
    const healthResponse = await handleRequest(request("/health/"), { ASSETS: assets });

    for (const response of [redirectResponse, healthResponse]) {
      expect(response.headers.get("content-security-policy")).toContain("frame-ancestors 'self'");
      expect(response.headers.get("x-frame-options")).toBe("SAMEORIGIN");
      expect(response.headers.get("permissions-policy")).toBe(
        "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
      );
    }
  });
});
