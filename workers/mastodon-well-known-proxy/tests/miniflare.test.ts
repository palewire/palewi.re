import { once } from "node:events";
import { createServer } from "node:net";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

let worker: ChildProcessWithoutNullStreams;
let output = "";
let port = 0;

async function availablePort(): Promise<number> {
  const server = createServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  server.close();
  if (address === null || typeof address === "string") {
    throw new Error("Could not reserve a Miniflare port.");
  }
  return address.port;
}

async function waitForWorker(): Promise<void> {
  const started = Date.now();
  while (Date.now() - started < 20_000) {
    if (worker.exitCode !== null) {
      throw new Error(`Miniflare exited before starting:\n${output}`);
    }
    try {
      const response = await fetch(`http://127.0.0.1:${port}/.well-known/nodeinfo`, {
        method: "POST",
      });
      if (response.status === 405) {
        return;
      }
    } catch {
      // The local workerd process is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Miniflare did not start:\n${output}`);
}

beforeAll(async () => {
  port = await availablePort();
  worker = spawn(
    process.execPath,
    ["./node_modules/wrangler/bin/wrangler.js", "dev", "--local", "--ip", "127.0.0.1", "--port", String(port)],
    { cwd: process.cwd() },
  );
  worker.stdout.on("data", (data: Buffer) => {
    output += data.toString();
  });
  worker.stderr.on("data", (data: Buffer) => {
    output += data.toString();
  });
  await waitForWorker();
});

afterAll(async () => {
  if (worker.exitCode === null) {
    worker.kill("SIGTERM");
    await once(worker, "exit");
  }
});

describe("Miniflare runtime", () => {
  it("starts the deployed module and handles a locally rejected request", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/.well-known/nodeinfo`, {
      method: "POST",
    });

    expect(response.status).toBe(405);
    expect(response.headers.get("x-palewire-discovery-proxy")).toBe("cloudflare-worker-v1");
  });
});
