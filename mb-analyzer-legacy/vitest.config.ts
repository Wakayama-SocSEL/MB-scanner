import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: [
      "apps/*/tests/**/*.test.ts",
      "features/*/tests/**/*.test.ts",
    ],
    environment: "node",
    passWithNoTests: true,
  },
});
