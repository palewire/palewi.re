import { readFileSync } from "node:fs";

import { describe, expect, it, vi } from "vitest";

import { handleRequest, type FetchImplementation } from "../src/index";

const BASE_URL = "https://palewi.re";
const MAX_RESPONSE_BYTES = 1_048_576;

function request(path: string, init?: RequestInit): Request {
  return new Request(`${BASE_URL}${path}`, init);
}

function fetchResponse(response: Response): FetchImplementation {
  return vi.fn().mockResolvedValue(response);
}

describe("Mastodon discovery Worker", () => {
  it("enables public same-zone fetches and configures a guarded canary", () => {
    const config = JSON.parse(readFileSync(new URL("../wrangler.jsonc", import.meta.url), "utf8"));

    expect(config.workers_dev).toBe(true);
    expect(config.preview_urls).toBe(true);
    expect(config.routes).toBeUndefined();
    expect(config.compatibility_flags).toContain("global_fetch_strictly_public");
    expect(config.env["same-zone-canary"].name).toBe("palewire-mastodon-well-known-proxy-same-zone-canary");
    expect(config.env["same-zone-canary"].vars).toEqual({
      CANARY_PATH: "/.well-known/cloudflare-worker-canary",
    });
  });

  it("only enables the canary path for the canary binding", async () => {
    const fetchMock = fetchResponse(new Response('{"links":[]}', {
      headers: { "content-type": "application/json; charset=utf-8" },
    }));

    const productionResponse = await handleRequest(
      request("/.well-known/cloudflare-worker-canary"),
      fetchMock,
    );
    expect(productionResponse.status).toBe(404);
    expect(fetchMock).not.toHaveBeenCalled();

    const canaryResponse = await handleRequest(
      request("/.well-known/cloudflare-worker-canary"),
      fetchMock,
      undefined,
      { CANARY_PATH: "/.well-known/cloudflare-worker-canary" },
    );
    expect(canaryResponse.status).toBe(200);
    expect(await canaryResponse.text()).toBe('{"links":[]}');
    expect(fetchMock).toHaveBeenCalledWith(
      new URL("https://mastodon.palewi.re/.well-known/nodeinfo"),
      expect.anything(),
    );
  });

  it("proxies WebFinger to the fixed upstream and preserves its safe response headers", async () => {
    const upstream = new Response('{"subject":"acct:palewire@palewi.re"}', {
      status: 200,
      headers: {
        "cache-control": "public, max-age=300",
        "content-type": "application/jrd+json",
        etag: '"v1"',
        vary: "Accept",
      },
    });
    const fetchMock = fetchResponse(upstream);
    const response = await handleRequest(
      request("/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re&rel=self", {
        headers: { accept: "application/jrd+json", "if-none-match": '"old"' },
      }),
      fetchMock,
    );

    expect(response.status).toBe(200);
    expect(await response.text()).toBe('{"subject":"acct:palewire@palewi.re"}');
    expect(response.headers.get("content-type")).toBe("application/jrd+json");
    expect(response.headers.get("cache-control")).toBe("public, max-age=300");
    expect(response.headers.get("etag")).toBe('"v1"');
    expect(response.headers.get("x-palewire-discovery-proxy")).toBe("cloudflare-worker-v1");

    expect(fetchMock).toHaveBeenCalledWith(
      new URL("https://mastodon.palewi.re/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re&rel=self"),
      expect.objectContaining({
        method: "GET",
        redirect: "manual",
        headers: expect.any(Headers),
      }),
    );
    const [, init] = vi.mocked(fetchMock).mock.calls[0];
    expect(new Headers(init?.headers).get("accept")).toBe("application/jrd+json");
    expect(new Headers(init?.headers).get("if-none-match")).toBe('"old"');
  });

  it("preserves host-meta query parameters without changing the trusted destination", async () => {
    const fetchMock = fetchResponse(new Response("<XRD />", { headers: { "content-type": "application/xrd+xml" } }));
    await handleRequest(request("/.well-known/host-meta?resource=acct%3Aalice%40palewi.re&ignored=https%3A%2F%2Fevil.example"), fetchMock);

    expect(fetchMock).toHaveBeenCalledWith(
      new URL(
        "https://mastodon.palewi.re/.well-known/host-meta?resource=acct%3Aalice%40palewi.re&ignored=https%3A%2F%2Fevil.example",
      ),
      expect.anything(),
    );
  });

  it("preserves upstream status and content type", async () => {
    const fetchMock = fetchResponse(
      new Response("<XRD />", {
        status: 202,
        headers: { "content-type": "application/xrd+xml; charset=utf-8", "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT" },
      }),
    );
    const response = await handleRequest(request("/.well-known/nodeinfo"), fetchMock);

    expect(response.status).toBe(202);
    expect(response.headers.get("content-type")).toBe("application/xrd+xml; charset=utf-8");
    expect(response.headers.get("last-modified")).toBe("Mon, 01 Jan 2024 00:00:00 GMT");
  });

  it("keeps HEAD requests bounded and forwards the method", async () => {
    const fetchMock = fetchResponse(
      new Response(null, { status: 200, headers: { "content-length": "42", "content-type": "application/jrd+json" } }),
    );
    const response = await handleRequest(
      request("/.well-known/webfinger?resource=acct%3Apalewire%40palewi.re", { method: "HEAD" }),
      fetchMock,
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-length")).toBe("42");
    expect(await response.text()).toBe("");
    expect(vi.mocked(fetchMock).mock.calls[0][1]?.method).toBe("HEAD");
  });

  it("returns a timeout without exposing upstream details", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn(
      (_input: RequestInfo | URL, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    );
    const result = handleRequest(request("/.well-known/nodeinfo"), fetchMock, 10);
    await vi.runAllTimersAsync();
    const response = await result;
    vi.useRealTimers();

    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ error: "upstream request timed out" });
  });

  it("keeps the timeout active while reading a slow upstream body", async () => {
    vi.useFakeTimers();
    let streamController: ReadableStreamDefaultController<Uint8Array> | undefined;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        streamController = controller;
      },
    });
    const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      init?.signal?.addEventListener("abort", () => streamController?.error(new DOMException("aborted", "AbortError")));
      return Promise.resolve(new Response(stream));
    });
    const result = handleRequest(request("/.well-known/nodeinfo"), fetchMock, 10);
    await vi.runAllTimersAsync();
    const response = await result;
    vi.useRealTimers();

    expect(response.status).toBe(504);
    expect(await response.json()).toEqual({ error: "upstream request timed out" });
  });

  it("rejects an upstream response with an oversized declared length", async () => {
    const fetchMock = fetchResponse(
      new Response("small", { headers: { "content-length": String(MAX_RESPONSE_BYTES + 1) } }),
    );
    const response = await handleRequest(request("/.well-known/nodeinfo"), fetchMock);

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ error: "upstream response exceeded size limit" });
  });

  it("rejects an oversized streamed upstream response", async () => {
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new Uint8Array(MAX_RESPONSE_BYTES));
        controller.enqueue(new Uint8Array([1]));
        controller.close();
      },
    });
    const fetchMock = fetchResponse(new Response(stream));
    const response = await handleRequest(request("/.well-known/nodeinfo"), fetchMock);

    expect(response.status).toBe(502);
    expect(await response.json()).toEqual({ error: "upstream response exceeded size limit" });
  });

  it("rejects upstream redirects instead of following them", async () => {
    const fetchMock = fetchResponse(new Response(null, { status: 302, headers: { location: "https://evil.example/" } }));
    const response = await handleRequest(request("/.well-known/nodeinfo"), fetchMock);

    expect(response.status).toBe(502);
    expect(response.headers.get("location")).toBeNull();
    expect(await response.json()).toEqual({ error: "upstream redirect rejected" });
  });

  it.each([
    ["/.well-known/webfinger", 400, "invalid webfinger resource"],
    ["/.well-known/webfinger?resource=acct%3Aalice%40example.com", 400, "invalid webfinger resource"],
    ["/.well-known/webfinger?resource=acct%3Aalice%40palewi.re&resource=acct%3Abob%40palewi.re", 400, "invalid webfinger resource"],
    ["/.well-known/unknown", 404, "not found"],
  ])("rejects invalid request %s", async (path, status, error) => {
    const fetchMock = vi.fn();
    const response = await handleRequest(request(path), fetchMock);

    expect(response.status).toBe(status);
    expect(await response.json()).toEqual({ error });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects unsupported methods with an Allow header", async () => {
    const fetchMock = vi.fn();
    const response = await handleRequest(request("/.well-known/nodeinfo", { method: "POST" }), fetchMock);

    expect(response.status).toBe(405);
    expect(response.headers.get("allow")).toBe("GET, HEAD");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns a bounded generic failure when the upstream request fails", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("private upstream error"));
    const response = await handleRequest(request("/.well-known/nodeinfo"), fetchMock);

    expect(response.status).toBe(502);
    const body = await response.text();
    expect(body).toBe('{"error":"upstream request failed"}');
    expect(body).not.toContain("private upstream error");
  });
});
