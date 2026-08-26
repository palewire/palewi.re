export interface StaticAssets {
  fetch(request: Request): Promise<Response>;
}

export interface WorkerEnvironment {
  ASSETS: StaticAssets;
}

const CANONICAL_HOST = "palewi.re";
const SIBLING_HOSTS = new Set(["www.palewi.re", "palewire.com", "www.palewire.com"]);
const USERNAME_DESTINATION = "https://mastodon.palewi.re/@palewire";
const SECURITY_TXT_PATH = "/.well-known/security.txt";
const CONTENT_SECURITY_POLICY = [
  "base-uri 'self'",
  "default-src 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
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
  "x-frame-options": "DENY",
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
  return withSecurityHeaders(await environment.ASSETS.fetch(request), request);
}

export default {
  fetch(request: Request, environment: WorkerEnvironment): Promise<Response> {
    return handleRequest(request, environment);
  },
};
