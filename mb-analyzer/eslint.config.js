import js from "@eslint/js";
import tseslint from "typescript-eslint";
import importPlugin from "eslint-plugin-import";
import globals from "globals";

// 機能間の依存方向ルール。
// - shared/ は他の機能ディレクトリを import してはならない（末端層）
// - equivalence-checker/ は pruning/ 等の将来機能を import してはならない
// - cli/ のみ composition root として全機能を import できる
const DEPENDENCY_ZONES = [
  {
    target: "./src/shared",
    from: [
      "./src/equivalence-checker",
      "./src/pruning",
      "./src/equivalence-class-test",
      "./src/eslint-rule-codegen",
      "./src/cli",
    ],
  },
  {
    target: "./src/equivalence-checker",
    from: ["./src/pruning", "./src/equivalence-class-test", "./src/eslint-rule-codegen", "./src/cli"],
  },
  {
    target: "./src/pruning",
    from: ["./src/equivalence-class-test", "./src/eslint-rule-codegen", "./src/cli"],
  },
  {
    target: "./src/equivalence-class-test",
    from: ["./src/eslint-rule-codegen", "./src/cli"],
  },
  {
    target: "./src/eslint-rule-codegen",
    from: ["./src/cli"],
  },
];

export default tseslint.config(
  {
    ignores: ["dist/**", "node_modules/**", "coverage/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.node,
      },
    },
    plugins: {
      import: importPlugin,
    },
    settings: {
      "import/resolver": {
        typescript: {
          project: "./tsconfig.json",
        },
      },
    },
    rules: {
      "import/no-restricted-paths": ["error", { zones: DEPENDENCY_ZONES }],
      "@typescript-eslint/consistent-type-imports": "error",
    },
  },
  {
    files: ["tests/**/*.ts"],
    rules: {
      "@typescript-eslint/no-unsafe-assignment": "off",
      "@typescript-eslint/no-unsafe-member-access": "off",
    },
  },
  {
    files: ["build.mjs", "eslint.config.js", "vitest.config.ts"],
    languageOptions: {
      parserOptions: {
        projectService: false,
      },
      globals: {
        ...globals.node,
      },
    },
    ...tseslint.configs.disableTypeChecked,
  },
);
