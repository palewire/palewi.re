import { parse } from "yaml";

import manifestText from "../../../project/redirects.yaml";

const MARKER = "cloudflare-worker-v1";
const ROUTE_HOST = "palewi.re";
const ROUTE_LIMIT = 100;
const CAPTURE_PATTERNS = {
  digits: "[0-9]+",
  digits2: "[0-9]{2}",
  digits4: "[0-9]{4}",
  path: ".+",
  segment: "[^/]+",
  slug: "[-\\w]+",
} as const;
const TEMPLATE = /\{([a-z][a-z0-9_]*)\}/g;
const WHOLE_TEMPLATE = /^\{[a-z][a-z0-9_]*\}$/;

type CaptureKind = keyof typeof CAPTURE_PATTERNS;

interface ManifestRecord {
  source: string;
  destination: string;
  captures?: Record<string, CaptureKind>;
  routes?: string[];
  examples?: string[];
}

interface Manifest {
  redirects: ManifestRecord[];
}

export interface RedirectRule {
  source: string;
  destination: string;
  captures: Record<string, CaptureKind>;
  routes: string[];
  examples: string[];
  matcher: RegExp;
}

export interface WorkerEnvironment {
  CANARY_PATH?: string;
}

export class RedirectManifestError extends Error {}

function templateNames(value: string): string[] {
  return [...value.matchAll(TEMPLATE)].map((match) => match[1]);
}

function sourcePattern(source: string, captures: Record<string, CaptureKind>): RegExp {
  let position = 0;
  let pattern = "^/";
  for (const match of source.matchAll(TEMPLATE)) {
    pattern += escapeRegex(source.slice(position, match.index));
    pattern += `(?<${match[1]}>${CAPTURE_PATTERNS[captures[match[1]]]})`;
    position = (match.index ?? 0) + match[0].length;
  }
  return new RegExp(`${pattern}${escapeRegex(source.slice(position))}$`, "u");
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function validateSource(source: string, index: number): void {
  if (source.startsWith("/") || source.includes("*") || source.includes("?") || source.includes("#")) {
    throw new RedirectManifestError(`redirect ${index}: source must be a relative path without query strings or fragments`);
  }
  if (source.startsWith("../") || source.includes("/../") || source.includes("//")) {
    throw new RedirectManifestError(`redirect ${index}: source contains an unsafe or malformed path segment`);
  }
  const withoutTemplates = source.replace(TEMPLATE, "");
  if (withoutTemplates.includes("{") || withoutTemplates.includes("}")) {
    throw new RedirectManifestError(`redirect ${index}: source has an invalid capture template`);
  }
}

function validateDestination(destination: string, index: number): void {
  if (destination.startsWith("/")) {
    if (destination.startsWith("//") || destination.includes("?") || destination.includes("#")) {
      throw new RedirectManifestError(`redirect ${index}: relative destination must be a path without query strings or fragments`);
    }
    return;
  }
  let url: URL;
  try {
    url = new URL(destination);
  } catch {
    throw new RedirectManifestError(`redirect ${index}: destination must be an absolute HTTP(S) URL or an absolute path`);
  }
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new RedirectManifestError(`redirect ${index}: destination must use an HTTP(S) scheme`);
  }
}

function sourcesOverlap(left: RedirectRule, right: RedirectRule): boolean {
  const leftParts = left.source.replace(/^\/|\/$/g, "").split("/");
  const rightParts = right.source.replace(/^\/|\/$/g, "").split("/");
  if (leftParts.length !== rightParts.length) {
    return false;
  }
  return leftParts.every((part, index) => {
    const other = rightParts[index];
    return WHOLE_TEMPLATE.test(part) || WHOLE_TEMPLATE.test(other) || part === other;
  });
}

function replaceDestination(rule: RedirectRule, match: RegExpExecArray): string {
  return rule.destination.replace(TEMPLATE, (_template, name: string) => match.groups?.[name] ?? "");
}

function validCaptureKinds(captures: object): captures is Record<string, CaptureKind> {
  return Object.values(captures).every((value) => typeof value === "string" && value in CAPTURE_PATTERNS);
}

export function loadManifest(text: string): RedirectRule[] {
  let raw: unknown;
  try {
    raw = parse(text);
  } catch (error) {
    throw new RedirectManifestError(`invalid YAML: ${error instanceof Error ? error.message : String(error)}`);
  }
  if (typeof raw !== "object" || raw === null || !("redirects" in raw) || !Array.isArray(raw.redirects)) {
    throw new RedirectManifestError("expected a single 'redirects' list");
  }
  const records = raw.redirects as unknown[];
  const rules = records.map((record, offset) => {
    const index = offset + 1;
    if (typeof record !== "object" || record === null || Array.isArray(record)) {
      throw new RedirectManifestError(`redirect ${index}: record must be a mapping`);
    }
    const value = record as Record<string, unknown>;
    const unknown = Object.keys(value).filter((key) => !["source", "destination", "captures", "routes", "examples"].includes(key));
    if (unknown.length > 0) {
      throw new RedirectManifestError(`redirect ${index}: unknown fields: ${unknown.join(", ")}`);
    }
    if (typeof value.source !== "string" || !value.source || typeof value.destination !== "string" || !value.destination) {
      throw new RedirectManifestError(`redirect ${index}: source and destination must be non-empty strings`);
    }
    validateSource(value.source, index);
    validateDestination(value.destination, index);
    const names = templateNames(value.source);
    const captures = value.captures ?? {};
    if (typeof captures !== "object" || captures === null || Array.isArray(captures) || !validCaptureKinds(captures)) {
      throw new RedirectManifestError(`redirect ${index}: captures must use known capture types`);
    }
    const captureMap = captures as Record<string, CaptureKind>;
    if (Object.keys(captureMap).sort().join(",") !== [...new Set(names)].sort().join(",")) {
      throw new RedirectManifestError(`redirect ${index}: captures must name every source template exactly once`);
    }
    if (templateNames(value.destination).some((name) => !names.includes(name))) {
      throw new RedirectManifestError(`redirect ${index}: destination references an unknown capture`);
    }
    const routes = value.routes ?? [];
    if (!Array.isArray(routes) || routes.some((route) => typeof route !== "string" || !route)) {
      throw new RedirectManifestError(`redirect ${index}: routes must be a list of non-empty path prefixes`);
    }
    if (routes.some((route) => route.startsWith("/") || route.includes("*") || route.includes("?") || route.includes("#"))) {
      throw new RedirectManifestError(`redirect ${index}: routes must be literal relative path prefixes`);
    }
    if (names.length > 0 && routes.length === 0) {
      throw new RedirectManifestError(`redirect ${index}: dynamic redirects require explicit Cloudflare route prefixes`);
    }
    if (names.length === 0 && routes.length > 0) {
      throw new RedirectManifestError(`redirect ${index}: exact redirects derive their Cloudflare route automatically`);
    }
    if (names.length > 0) {
      const staticPrefix = value.source.split("{", 1)[0];
      const expectedRoutes = value.source.startsWith("{year}") && captureMap.year === "digits4"
        ? new Set(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
        : new Set([staticPrefix]);
      if (routes.length !== expectedRoutes.size || routes.some((route) => !expectedRoutes.has(route))) {
        throw new RedirectManifestError(`redirect ${index}: routes do not safely cover the dynamic source`);
      }
    }
    const examples = value.examples ?? [];
    if (!Array.isArray(examples) || examples.some((example) => typeof example !== "string")) {
      throw new RedirectManifestError(`redirect ${index}: examples must be a list of paths`);
    }
    if (names.length > 0 && examples.length === 0) {
      throw new RedirectManifestError(`redirect ${index}: dynamic redirects require boundary examples`);
    }
    const rule: RedirectRule = {
      source: value.source,
      destination: value.destination,
      captures: captureMap,
      routes,
      examples,
      matcher: sourcePattern(value.source, captureMap),
    };
    for (const example of rule.examples) {
      if (!example.startsWith("/") || !rule.matcher.test(example)) {
        throw new RedirectManifestError(`redirect ${index}: example ${JSON.stringify(example)} is not covered by its source`);
      }
      if (!rule.routes.some((route) => example.startsWith(`/${route}`))) {
        throw new RedirectManifestError(`redirect ${index}: route coverage gap for ${JSON.stringify(example)}`);
      }
    }
    if (rule.destination.startsWith("/") && rule.destination.slice(1) === rule.source) {
      throw new RedirectManifestError(`redirect ${index}: redirect loops to itself`);
    }
    return rule;
  });
  rules.forEach((rule, index) => {
    rules.slice(0, index).forEach((prior) => {
      if (sourcesOverlap(prior, rule)) {
        throw new RedirectManifestError(`redirect ${index + 1}: source overlaps ${JSON.stringify(prior.source)}`);
      }
    });
  });
  const routePlan = new Set([
    ...rules.filter((rule) => Object.keys(rule.captures).length === 0).map((rule) => `${ROUTE_HOST}/${rule.source}*`),
    ...rules.flatMap((rule) => rule.routes.map((route) => `${ROUTE_HOST}/${route}*`)),
  ]);
  if (routePlan.size > ROUTE_LIMIT) {
    throw new RedirectManifestError(`redirect route plan exceeds the ${ROUTE_LIMIT}-route safety limit`);
  }
  if (routePlan.has(`${ROUTE_HOST}/*`)) {
    throw new RedirectManifestError("redirect route plan must not use a broad site-wide route");
  }
  return rules;
}

export const rules = loadManifest(manifestText);
export const routePlan = [
  ...new Set([
    ...rules.filter((rule) => Object.keys(rule.captures).length === 0).map((rule) => `${ROUTE_HOST}/${rule.source}*`),
    ...rules.flatMap((rule) => rule.routes.map((route) => `${ROUTE_HOST}/${route}*`)),
  ]),
];

function response(status: number, body: string | null, headers: HeadersInit = {}): Response {
  return new Response(body, {
    status,
    headers: {
      "cache-control": "no-store",
      ...headers,
    },
  });
}

export function handleRequest(request: Request, environment: WorkerEnvironment = {}): Response {
  const url = new URL(request.url);
  if (environment.CANARY_PATH === url.pathname) {
    return response(204, null, { "x-palewire-legacy-redirect": MARKER });
  }
  if (request.method !== "GET" && request.method !== "HEAD") {
    return response(405, "method not allowed", { allow: "GET, HEAD" });
  }
  for (const rule of rules) {
    const match = rule.matcher.exec(url.pathname);
    if (match !== null) {
      return response(302, "", {
        location: replaceDestination(rule, match),
        "x-palewire-legacy-redirect": MARKER,
      });
    }
  }
  return response(404, "not found");
}

export default {
  fetch(request: Request, environment: WorkerEnvironment): Response {
    return handleRequest(request, environment);
  },
};
