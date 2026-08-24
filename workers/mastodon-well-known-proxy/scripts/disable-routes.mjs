const API_ORIGIN = "https://api.cloudflare.com/client/v4";
const ZONE_NAME = "palewi.re";
const WORKER_NAME = "palewire-mastodon-well-known-proxy";
const EXPECTED_PATTERNS = new Set([
  "palewi.re/.well-known/webfinger*",
  "palewi.re/.well-known/host-meta*",
  "palewi.re/.well-known/nodeinfo*",
]);

const token = process.env.CLOUDFLARE_API_TOKEN;
if (process.env.CONFIRM_WORKER_ROLLBACK !== "1") {
  throw new Error("Set CONFIRM_WORKER_ROLLBACK=1 to remove the three Worker routes.");
}
if (!token) {
  throw new Error("CLOUDFLARE_API_TOKEN is required.");
}

async function request(path, options = {}) {
  const response = await fetch(`${API_ORIGIN}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`Cloudflare API request failed with HTTP ${response.status}.`);
  }
  const payload = await response.json();
  if (!payload.success) {
    throw new Error("Cloudflare API request was unsuccessful.");
  }
  return payload.result;
}

const zones = await request(`/zones?name=${ZONE_NAME}&status=active`);
if (zones.length !== 1) {
  throw new Error(`Expected one active ${ZONE_NAME} zone.`);
}

const zoneId = zones[0].id;
const routes = await request(`/zones/${zoneId}/workers/routes`);
const workerRoutes = routes.filter((route) => route.script === WORKER_NAME);
const routesToDelete = routes.filter((route) => route.script === WORKER_NAME && EXPECTED_PATTERNS.has(route.pattern));
if (workerRoutes.length !== EXPECTED_PATTERNS.size || routesToDelete.length !== EXPECTED_PATTERNS.size) {
  throw new Error("Expected this Worker to have only the three configured routes; no routes were changed.");
}

for (const route of routesToDelete) {
  await request(`/zones/${zoneId}/workers/routes/${route.id}`, { method: "DELETE" });
}

const remainingRoutes = await request(`/zones/${zoneId}/workers/routes`);
if (remainingRoutes.some((route) => route.script === WORKER_NAME)) {
  throw new Error("Worker routes remain after rollback.");
}

console.log("Removed the three Mastodon discovery Worker routes. Django fallback is active.");
