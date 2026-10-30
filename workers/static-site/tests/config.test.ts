import { describe, expect, it } from "vitest";

import cloudflareConfig from "../cloudflare.config";
import wranglerConfig from "../wrangler.config";

const productionRoutes = [
  { pattern: "palewi.re/*", zone: "palewi.re" },
  { pattern: "www.palewi.re/*", zone: "palewi.re" },
  { pattern: "palewire.com/*", zone: "palewire.com" },
  { pattern: "www.palewire.com/*", zone: "palewire.com" },
];

describe("static-site deployment configuration", () => {
  it.each([undefined, "production"])(
    "uses the production worker and its four original routes for mode %s",
    (mode) => {
      const { worker } = cloudflareConfig({ mode, isPreview: false });

      expect(worker.name).toBe("palewire-static-site");
      expect(worker.workersDev).toBe(false);
      expect(worker.previewUrls).toBe(false);
      expect(worker.triggers).toMatchObject(productionRoutes);
    },
  );

  it("keeps the named preview worker route-free and isolated from production", () => {
    const { worker } = cloudflareConfig({ mode: "preview", isPreview: false });

    expect(worker.name).toBe("palewire-static-site-preview");
    expect(worker.workersDev).toBe(true);
    expect(worker.previewUrls).toBe(true);
    expect(worker.triggers).toEqual([]);
    expect(worker.name).not.toBe("palewire-static-site");
  });

  it("rejects Worker Previews and unknown modes", () => {
    expect(() => cloudflareConfig({ mode: "production", isPreview: true })).toThrow(
      "Use the named static-site preview mode instead of Worker Previews.",
    );
    expect(() => cloudflareConfig({ mode: "unexpected", isPreview: false })).toThrow(
      "Unknown static-site Worker mode: unexpected",
    );
  });

  it.each([undefined, "production", "preview"])(
    "keeps shared asset and R2 settings in mode %s",
    (mode) => {
      const { worker } = cloudflareConfig({ mode, isPreview: false });

      expect(worker.assets).toEqual({
        htmlHandling: "auto-trailing-slash",
        notFoundHandling: "404-page",
        runWorkerFirst: true,
      });
      expect(worker.env.TALK_MEDIA).toEqual({
        type: "r2",
        name: "palewire-talk-media",
        dev: { remote: true },
      });
      expect(worker.env.ASSETS).toEqual({ type: "assets" });
    },
  );

  it("sets the static asset directory in Wrangler's tooling config", () => {
    expect(wranglerConfig).toHaveProperty("assetsDirectory", "../../dist");
  });
});
