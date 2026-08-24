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
      const response = await fetch(`http://127.0.0.1:${port}/feed/`, { redirect: "manual" });
      if (response.status === 302) {
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
}, 30_000);

afterAll(async () => {
  if (worker.exitCode === null) {
    worker.kill("SIGTERM");
    await once(worker, "exit");
  }
});

describe("Miniflare runtime", () => {
  it("starts the bundled manifest Worker without fetching and preserves the redirect response", async () => {
    const response = await fetch(`http://127.0.0.1:${port}/images/space%20name.jpg?source=test`, {
      redirect: "manual",
    });

    expect(response.status).toBe(302);
    expect(response.headers.get("location")).toBe("https://palewire.s3.amazonaws.com/img/space%20name.jpg");
    expect(response.headers.get("x-palewire-legacy-redirect")).toBe("cloudflare-worker-v1");
  });
});
