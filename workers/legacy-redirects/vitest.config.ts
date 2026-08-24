import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    {
      name: "yaml-as-text",
      enforce: "pre",
      transform(source, id) {
        if (id.endsWith(".yaml")) {
          return `export default ${JSON.stringify(source)};`;
        }
      },
    },
  ],
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    testTimeout: 30_000,
  },
});
