import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { once } from "node:events";
import { readFileSync } from "node:fs";
import { createServer } from "node:net";
import { resolve } from "node:path";

import { afterAll, beforeAll, expect, it } from "vitest";

let worker: ChildProcessWithoutNullStreams;
let output = "";
let port = 0;

beforeAll(async () => {
  const server = createServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  server.close();
  if (address === null || typeof address === "string") {
    throw new Error("Could not reserve a static Worker port.");
  }
  port = address.port;
  worker = spawn(process.execPath, ["./node_modules/cf/bin/cf", "dev"], {
    cwd: process.cwd(),
    env: { ...process.env, STATIC_DEV_PORT: String(port), STATIC_WORKER_LOCAL: "1" },
  });
  worker.stdout.on("data", (data: Buffer) => { output += data.toString(); });
  worker.stderr.on("data", (data: Buffer) => { output += data.toString(); });
  const started = Date.now();
  while (Date.now() - started < 20_000) {
    if (worker.exitCode !== null) {
      throw new Error(`Static Worker exited before starting:\n${output}`);
    }
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health/`, {
        signal: AbortSignal.timeout(2_000),
      });
      if (response.ok && (await response.text()) === '{"status":"ok"}') return;
    } catch {
      // Vite and workerd are still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`Static Worker did not start:\n${output}`);
}, 30_000);

afterAll(async () => {
  if (worker.exitCode === null) {
    worker.kill("SIGTERM");
    await once(worker, "exit");
  }
});

it("serves baked HTML, stylesheet bytes and the custom 404 through Vite and workerd", async () => {
  const base = `http://127.0.0.1:${port}`;
  const page = await fetch(`${base}/who-is-ben-welsh/`);
  expect(page.status).toBe(200);
  expect(await page.text()).toContain('href="https://palewi.re/who-is-ben-welsh/"');
  expect(page.headers.get("content-security-policy")).toContain("default-src 'self'");

  const stylesheet = await fetch(`${base}/static/styles.css`);
  expect(stylesheet.status).toBe(200);
  expect(stylesheet.headers.get("content-type")).toContain("text/css");
  expect(Buffer.from(await stylesheet.arrayBuffer())).toEqual(
    readFileSync(resolve(process.cwd(), "../../dist/static/styles.css")),
  );

  const missing = await fetch(`${base}/this-page-does-not-exist/`);
  expect(missing.status).toBe(404);
  expect(await missing.text()).toContain('id="error-heading">404<');

  const root = await fetch(`${base}/`, { redirect: "manual" });
  expect(root.status).toBe(302);
  expect(root.headers.get("location")).toBe("/who-is-ben-welsh/");
});
