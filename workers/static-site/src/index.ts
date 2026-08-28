export interface StaticAssets {
  fetch(request: Request): Promise<Response>;
}

export interface TalkMediaObject {
  body: ReadableStream | null;
  httpEtag: string;
  range?: { length: number; offset: number };
  size: number;
  writeHttpMetadata(headers: Headers): void;
}

export interface TalkMedia {
  get(key: string, options?: { range?: Headers }): Promise<TalkMediaObject | null>;
  head(key: string): Promise<TalkMediaObject | null>;
}

export interface WorkerEnvironment {
  ASSETS: StaticAssets;
  TALK_MEDIA?: TalkMedia;
}

const CANONICAL_HOST = "palewi.re";
const SIBLING_HOSTS = new Set(["www.palewi.re", "palewire.com", "www.palewire.com"]);
const USERNAME_DESTINATION = "https://mastodon.palewi.re/@palewire";
const SECURITY_TXT_PATH = "/.well-known/security.txt";
const CONTENT_SECURITY_POLICY = [
  "base-uri 'self'",
  "default-src 'self'",
  "form-action 'self'",
  "frame-ancestors 'self'",
  "frame-src 'self' https://datawrapper.dwcdn.net https://docs.google.com https://player.vimeo.com http://s3-us-west-1.amazonaws.com https://w.soundcloud.com",
  "img-src 'self' https://palewi.re http://chart.apis.google.com http://www.palewire.com https://palewire.s3.amazonaws.com",
  "font-src 'self' https://fonts.gstatic.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "script-src 'self'",
  "media-src 'self' https://palewire.s3.amazonaws.com",
  "object-src 'none'",
].join("; ");
const SECURITY_HEADERS = {
  "content-security-policy": CONTENT_SECURITY_POLICY,
  "permissions-policy": "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
  "referrer-policy": "strict-origin-when-cross-origin",
  "x-content-type-options": "nosniff",
  "x-frame-options": "SAMEORIGIN",
};

function redirect(destination: string, status: 301 | 302): Response {
  return new Response(null, {
    status,
    headers: {
      location: destination,
      ...SECURITY_HEADERS,
    },
  });
}

function withSecurityHeaders(response: Response, request: Request): Response {
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    headers.set(name, value);
  }
  if (new URL(request.url).protocol === "https:") {
    headers.set("strict-transport-security", "max-age=31536000; includeSubDomains; preload");
  }
  return new Response(response.body, {
    headers,
    status: response.status,
    statusText: response.statusText,
  });
}

function healthCheck(): Response {
  return Response.json(
    { status: "ok" },
    {
      headers: {
        "cache-control": "no-store",
        ...SECURITY_HEADERS,
      },
    },
  );
}

async function serveFeed(request: Request, assets: StaticAssets): Promise<Response> {
  const assetUrl = new URL(request.url);
  assetUrl.pathname = "/feeds/posts/index.xml";
  const response = await assets.fetch(new Request(assetUrl, request));
  const headers = new Headers(response.headers);
  headers.set("content-type", "application/rss+xml; charset=utf-8");
  return new Response(response.body, {
    headers,
    status: response.status,
    statusText: response.statusText,
  });
}

async function serveSecurityTxt(request: Request, assets: StaticAssets): Promise<Response> {
  const response = await assets.fetch(request);
  const headers = new Headers(response.headers);
  headers.set("content-type", "text/plain; charset=utf-8");
  return new Response(response.body, {
    headers,
    status: response.status,
    statusText: response.statusText,
  });
}

async function serveTalkMedia(request: Request, media: TalkMedia | undefined): Promise<Response> {
  if (!media) {
    throw new Error("TALK_MEDIA binding is not configured");
  }
  const key = new URL(request.url).pathname.slice("/media/".length);
  const object =
    request.method === "HEAD" ? await media.head(key) : await media.get(key, { range: request.headers });
  if (!object) {
    return new Response("Not found", { status: 404 });
  }

  const headers = new Headers({ "cache-control": "public, max-age=31536000, immutable" });
  object.writeHttpMetadata(headers);
  headers.set("etag", object.httpEtag);
  if (object.range) {
    headers.set("content-length", String(object.range.length));
    headers.set("content-range", `bytes ${object.range.offset}-${object.range.offset + object.range.length - 1}/${object.size}`);
  }
  return new Response(request.method === "HEAD" ? null : object.body, {
    headers,
    status: object.range ? 206 : 200,
  });
}

export async function handleRequest(request: Request, environment: WorkerEnvironment): Promise<Response> {
  const url = new URL(request.url);
  if (SIBLING_HOSTS.has(url.hostname)) {
    url.protocol = "https:";
    url.hostname = CANONICAL_HOST;
    return redirect(url.toString(), 301);
  }
  if (url.pathname === "/health/") {
    return healthCheck();
  }
  if (url.pathname === "/") {
    return redirect("/who-is-ben-welsh/", 302);
  }
  if (url.pathname === "/favicon.ico") {
    return redirect("/static/favicon.ico", 302);
  }
  if (url.pathname === "/@palewire") {
    return redirect(USERNAME_DESTINATION, 302);
  }
  if (url.pathname === "/feeds/posts/") {
    return withSecurityHeaders(await serveFeed(request, environment.ASSETS), request);
  }
  if (url.pathname === SECURITY_TXT_PATH) {
    return withSecurityHeaders(await serveSecurityTxt(request, environment.ASSETS), request);
  }
  if (url.pathname.startsWith("/media/talks/")) {
    return withSecurityHeaders(await serveTalkMedia(request, environment.TALK_MEDIA), request);
  }
  return withSecurityHeaders(await environment.ASSETS.fetch(request), request);
}

export default {
  fetch(request: Request, environment: WorkerEnvironment): Promise<Response> {
    return handleRequest(request, environment);
  },
};
