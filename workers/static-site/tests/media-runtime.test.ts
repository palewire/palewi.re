import { URL as NodeURL, fileURLToPath } from "node:url";
import { build } from "esbuild";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";
import { expect, it } from "vitest";

it("preserves byte ranges and HEAD responses with real R2 runtime objects", async () => {
  const bundle = await build({
    stdin: {
      resolveDir: fileURLToPath(new NodeURL("../src/", import.meta.url)),
      contents: `import worker from "./index.ts";
        export default {
          async fetch(request, env) {
            if (new URL(request.url).pathname === "/__seed") {
              const bytes = new Uint8Array(1000).map((_, index) => index % 256);
              await env.TALK_MEDIA.put("talks/runtime/video.mp4", bytes,
                { httpMetadata: { contentType: "video/mp4" } });
              return new Response("seeded");
            }
            return worker.fetch(request, env);
          }
        };`,
      loader: "js",
    },
    bundle: true,
    write: false,
    format: "esm",
    target: "es2022",
  });
  const runtime = new Miniflare(convertV4MiniflareOptions({
    modules: true,
    script: bundle.outputFiles[0].text,
    compatibilityDate: "2026-08-25",
    r2Buckets: ["TALK_MEDIA"],
  }));
  try {
    const seeded = await runtime.dispatchFetch("https://palewi.re/__seed");
    expect(await seeded.text()).toBe("seeded");
    for (const [range, expected] of [
      ["bytes=0-99", "bytes 0-99/1000"],
      ["bytes=900-", "bytes 900-999/1000"],
      ["bytes=-100", "bytes 900-999/1000"],
    ]) {
      const response = await runtime.dispatchFetch("https://palewi.re/media/talks/runtime/video.mp4", { headers: { range } });
      expect(response.status).toBe(206);
      expect(response.headers.get("content-range")).toBe(expected);
      expect(response.headers.get("content-length")).toBe("100");
      expect((await response.arrayBuffer()).byteLength).toBe(100);
    }
    const head = await runtime.dispatchFetch("https://palewi.re/media/talks/runtime/video.mp4", { method: "HEAD" });
    expect(head.status).toBe(206);
    expect(head.headers.get("content-range")).toBe("bytes 0-999/1000");
    expect(head.headers.get("content-length")).toBe("1000");
    expect(head.headers.get("content-type")).toBe("video/mp4");
    expect(await head.text()).toBe("");
  } finally {
    await runtime.dispose();
  }
});
