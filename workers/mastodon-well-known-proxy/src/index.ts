const UPSTREAM_ORIGIN = "https://mastodon.palewi.re";
const UPSTREAM_TIMEOUT_MS = 5_000;
const MAX_RESPONSE_BYTES = 1_048_576;
const RESPONSE_MARKER = "cloudflare-worker-v1";
const CANARY_PATH = "/.well-known/cloudflare-worker-canary";
const CANARY_UPSTREAM_PATH = "/.well-known/nodeinfo";

const ALLOWED_PATHS = new Set([
  "/.well-known/webfinger",
  "/.well-known/host-meta",
  "/.well-known/nodeinfo",
]);
const FORWARDED_REQUEST_HEADERS = ["accept", "if-none-match", "if-modified-since"];
const FORWARDED_RESPONSE_HEADERS = ["cache-control", "content-language", "content-type", "etag", "last-modified", "vary"];

export type FetchImplementation = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export interface WorkerEnvironment {
  CANARY_PATH?: string;
}

function errorResponse(status: number, message: string): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      "cache-control": "no-store",
      "content-type": "application/json; charset=utf-8",
      "x-palewire-discovery-proxy": RESPONSE_MARKER,
    },
  });
}

function isValidWebFingerRequest(url: URL): boolean {
  const resources = url.searchParams.getAll("resource");
  return resources.length === 1 && /^acct:[A-Za-z0-9._-]{1,64}@palewi\.re$/i.test(resources[0]);
}

function isCanaryRequest(url: URL, environment: WorkerEnvironment): boolean {
  return environment.CANARY_PATH === CANARY_PATH && url.pathname === CANARY_PATH;
}

function upstreamHeaders(request: Request): Headers {
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) {
      headers.set(name, value);
    }
  }
  return headers;
}

function declaredLength(response: Response): number | undefined {
  const value = response.headers.get("content-length");
  if (value === null || !/^\d+$/.test(value)) {
    return undefined;
  }
  return Number(value);
}

async function readBoundedBody(body: ReadableStream<Uint8Array> | null): Promise<Uint8Array> {
  if (body === null) {
    return new Uint8Array();
  }

  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      size += value.byteLength;
      if (size > MAX_RESPONSE_BYTES) {
        await reader.cancel("response exceeds size limit");
        throw new RangeError("response exceeds size limit");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result;
}

function responseHeaders(upstream: Headers): Headers {
  const headers = new Headers({
    "x-palewire-discovery-proxy": RESPONSE_MARKER,
  });
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.get(name);
    if (value !== null) {
      headers.set(name, value);
    }
  }
  return headers;
}

function log(outcome: string, request: Request, status: number, bytes = 0): void {
  console.log(
    JSON.stringify({
      event: "mastodon_discovery_proxy",
      outcome,
      method: request.method,
      path: new URL(request.url).pathname,
      status,
      bytes,
    }),
  );
}

export async function handleRequest(
  request: Request,
  fetchImplementation: FetchImplementation = fetch,
  timeoutMs = UPSTREAM_TIMEOUT_MS,
  environment: WorkerEnvironment = {},
): Promise<Response> {
  const requestUrl = new URL(request.url);
  const canaryRequest = isCanaryRequest(requestUrl, environment);
  if (!ALLOWED_PATHS.has(requestUrl.pathname) && !canaryRequest) {
    const response = errorResponse(404, "not found");
    log("invalid_path", request, response.status);
    return response;
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    const response = errorResponse(405, "method not allowed");
    response.headers.set("allow", "GET, HEAD");
    log("invalid_method", request, response.status);
    return response;
  }
  if (requestUrl.pathname === "/.well-known/webfinger" && !isValidWebFingerRequest(requestUrl)) {
    const response = errorResponse(400, "invalid webfinger resource");
    log("invalid_webfinger", request, response.status);
    return response;
  }

  const upstreamUrl = new URL(canaryRequest ? CANARY_UPSTREAM_PATH : requestUrl.pathname, UPSTREAM_ORIGIN);
  upstreamUrl.search = requestUrl.search;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  let receivedHeaders = false;

  try {
    const upstream = await fetchImplementation(upstreamUrl, {
      method: request.method,
      headers: upstreamHeaders(request),
      redirect: "manual",
      signal: controller.signal,
    });
    receivedHeaders = true;

    if (upstream.status >= 300 && upstream.status < 400) {
      const response = errorResponse(502, "upstream redirect rejected");
      log("upstream_redirect", request, response.status);
      return response;
    }

    const length = declaredLength(upstream);
    if (length !== undefined && length > MAX_RESPONSE_BYTES) {
      const response = errorResponse(502, "upstream response exceeded size limit");
      log("declared_response_too_large", request, response.status);
      return response;
    }

    const headers = responseHeaders(upstream.headers);
    if (request.method === "HEAD" || upstream.status === 204 || upstream.status === 205 || upstream.status === 304) {
      if (length !== undefined) {
        headers.set("content-length", String(length));
      }
      const response = new Response(null, { status: upstream.status, headers });
      log("success", request, response.status);
      return response;
    }

    const body = await readBoundedBody(upstream.body);
    headers.set("content-length", String(body.byteLength));
    const response = new Response(body, { status: upstream.status, headers });
    log("success", request, response.status, body.byteLength);
    return response;
  } catch (error) {
    const response = controller.signal.aborted || (error instanceof DOMException && error.name === "AbortError")
      ? errorResponse(504, "upstream request timed out")
      : error instanceof RangeError
      ? errorResponse(502, "upstream response exceeded size limit")
      : errorResponse(502, receivedHeaders ? "upstream response failed" : "upstream request failed");
    const outcome = response.status === 504
      ? "timeout"
      : error instanceof RangeError
        ? "response_too_large"
        : receivedHeaders
          ? "response_failure"
          : "upstream_failure";
    log(outcome, request, response.status);
    return response;
  } finally {
    clearTimeout(timeout);
  }
}

export default {
  fetch(request: Request, environment: WorkerEnvironment): Promise<Response> {
    return handleRequest(request, fetch, UPSTREAM_TIMEOUT_MS, environment);
  },
};
