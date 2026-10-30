import { defineWranglerConfig } from "wrangler/experimental-config";

export default defineWranglerConfig({
  rules: [{ type: "Text", globs: ["**/*.yaml"], fallthrough: false }],
  types: { generate: false },
});
