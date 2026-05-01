import * as esbuild from "esbuild";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const watch = process.argv.includes("--watch");

/** @type {import('esbuild').BuildOptions} */
const buildOptions = {
  entryPoints: [path.join(__dirname, "src", "cli", "index.ts")],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: path.join(__dirname, "dist", "cli.js"),
  target: "node22",
  external: ["vm"],
  // 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
  // minifySyntax は esbuild の `if (...)` DCE を起動するために必須 (esbuild #1955)
  define: {
    "import.meta.vitest": "undefined",
  },
  minifySyntax: true,
  banner: {
    js: [
      "import { createRequire as __topLevelCreateRequire } from 'module';",
      "const require = __topLevelCreateRequire(import.meta.url);",
      "import { fileURLToPath as __topLevelFileURLToPath } from 'url';",
      "import { dirname as __topLevelDirname } from 'path';",
      "const __filename = __topLevelFileURLToPath(import.meta.url);",
      "const __dirname = __topLevelDirname(__filename);",
    ].join("\n"),
  },
};

if (watch) {
  const ctx = await esbuild.context(buildOptions);
  await ctx.watch();
  console.log("Watching for changes...");
} else {
  await esbuild.build(buildOptions);
  console.log("Build complete: dist/cli.js");
}
