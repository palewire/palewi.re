import { spawn, spawnSync } from "node:child_process";
import { createServer, type Server } from "node:http";
import { once } from "node:events";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
let server: Server;
let baseUrl = "";
let nodeinfoMode: "normal" | "delayed-marker" | "missing-marker" | "server-error" = "normal";
let nodeinfoRequests = 0;

beforeAll(async () => {
  server = createServer((request, response) => {
    const path = new URL(request.url ?? "/", "http://fixture").pathname;
    const contentTypes: Record<string, string> = {
      "/.well-known/webfinger": "application/jrd+json; charset=utf-8",
      "/.well-known/host-meta": "application/xrd+xml; charset=utf-8",
      "/.well-known/nodeinfo": "application/json; charset=utf-8",
      "/.well-known/cloudflare-worker-canary": "application/json; charset=utf-8",
    };
    const contentType = contentTypes[path];
    if (contentType === undefined) {
      response.writeHead(404);
      response.end();
      return;
    }
    if (path === "/.well-known/nodeinfo") {
      nodeinfoRequests += 1;
      if (nodeinfoMode === "server-error") {
        response.writeHead(502, { "content-type": contentType });
        response.end();
        return;
      }
    }
    response.setHeader("content-type", contentType);
    const omitNodeinfoMarker =
      path === "/.well-known/nodeinfo" &&
      (nodeinfoMode === "missing-marker" || (nodeinfoMode === "delayed-marker" && nodeinfoRequests === 1));
    if (!omitNodeinfoMarker) {
      response.setHeader("x-palewire-discovery-proxy", "cloudflare-worker-v1");
    }
    response.end(path === "/.well-known/cloudflare-worker-canary" ? '{"links":[]}' : "{}");
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("Could not start endpoint fixture.");
  }
  baseUrl = `http://127.0.0.1:${address.port}`;
});

afterAll(async () => {
  server.close();
  await once(server, "close");
});

async function verify(
  environment: Record<string, string> = {},
): Promise<{ status: number | null; stdout: string; stderr: string }> {
  const child = spawn("make", ["worker-verify-production", `BASE_URL=${baseUrl}`], {
    cwd: repositoryRoot,
    env: { ...process.env, ...environment },
  });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (data: Buffer) => {
    stdout += data.toString();
  });
  child.stderr.on("data", (data: Buffer) => {
    stderr += data.toString();
  });
  const [status] = await once(child, "exit");
  return { status, stdout, stderr };
}

async function verifySameZoneCanary(): Promise<{ status: number | null; stdout: string; stderr: string }> {
  const child = spawn("make", ["worker-verify-same-zone-canary", `BASE_URL=${baseUrl}`], {
    cwd: repositoryRoot,
  });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (data: Buffer) => {
    stdout += data.toString();
  });
  child.stderr.on("data", (data: Buffer) => {
    stderr += data.toString();
  });
  const [status] = await once(child, "exit");
  return { status, stdout, stderr };
}

describe("worker verification target", () => {
  it("accepts all three valid Worker endpoint responses", async () => {
    const result = await verify();

    expect(result.status, result.stderr).toBe(0);
    expect(result.stdout).toContain("webfinger: HTTP 200 application/jrd+json; charset=utf-8");
    expect(result.stdout).toContain("host-meta: HTTP 200 application/xrd+xml; charset=utf-8");
    expect(result.stdout).toContain("nodeinfo: HTTP 200 application/json; charset=utf-8");
  });

  it("retries a delayed Worker marker and succeeds", async () => {
    nodeinfoMode = "delayed-marker";
    nodeinfoRequests = 0;
    const result = await verify({ WORKER_MARKER_ATTEMPTS: "2", WORKER_MARKER_WAIT_SECONDS: "0" });
    nodeinfoMode = "normal";

    expect(result.status, result.stderr).toBe(0);
    expect(nodeinfoRequests).toBe(2);
    expect(result.stderr).toContain("Worker marker not yet visible; waiting 0 seconds before retry 2 of 2.");
  });

  it("fails after the configured marker propagation attempts are exhausted", async () => {
    nodeinfoMode = "missing-marker";
    nodeinfoRequests = 0;
    const result = await verify({ WORKER_MARKER_ATTEMPTS: "3", WORKER_MARKER_WAIT_SECONDS: "0" });
    nodeinfoMode = "normal";

    expect(result.status).not.toBe(0);
    expect(nodeinfoRequests).toBe(3);
    expect(result.stderr).toContain("nodeinfo: Worker marker was not found");
    expect(result.stderr).toContain("Worker marker was not visible after 3 attempts.");
  });

  it("fails immediately for a true upstream server error", async () => {
    nodeinfoMode = "server-error";
    nodeinfoRequests = 0;
    const result = await verify({ WORKER_MARKER_ATTEMPTS: "3", WORKER_MARKER_WAIT_SECONDS: "0" });
    nodeinfoMode = "normal";

    expect(result.status).not.toBe(0);
    expect(nodeinfoRequests).toBe(1);
    expect(result.stderr).toContain("nodeinfo: expected HTTP 200, received 502");
    expect(result.stderr).not.toContain("Worker marker not yet visible");
  });

  it("accepts the guarded same-zone canary response", async () => {
    const result = await verifySameZoneCanary();

    expect(result.status).toBe(0);
    expect(result.stdout).toContain("same-zone canary: HTTP 200 application/json; charset=utf-8");
  });

  it.each([
    ["worker-canary-deploy", "CONFIRM_WORKER_CANARY_DEPLOY"],
    ["worker-delete-canary", "CONFIRM_WORKER_DELETE_CANARY"],
    ["worker-same-zone-canary-deploy", "CONFIRM_WORKER_SAME_ZONE_CANARY_DEPLOY"],
    ["worker-attach-same-zone-canary", "CONFIRM_WORKER_ATTACH_SAME_ZONE_CANARY"],
    ["worker-delete-same-zone-canary", "CONFIRM_WORKER_DELETE_SAME_ZONE_CANARY"],
    ["worker-attach-routes", "CONFIRM_WORKER_ATTACH_ROUTES"],
    ["worker-detach-routes", "CONFIRM_WORKER_DETACH_ROUTES"],
    ["worker-delete", "CONFIRM_WORKER_DELETE"],
  ])("requires %s confirmation before changing Cloudflare", (target, confirmation) => {
    const result = spawnSync("make", [target], {
      cwd: repositoryRoot,
      encoding: "utf8",
    });

    expect(result.status).not.toBe(0);
    expect(result.stderr).toContain(`Set ${confirmation}=1`);
  });
});
