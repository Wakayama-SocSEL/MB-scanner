import * as esbuild from "esbuild";
import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const watch = process.argv.includes("--watch");

/** @type {import('esbuild').BuildOptions} */
const buildOptions = {
  entryPoints: [path.join(__dirname, "src", "index.ts")],
  bundle: true,
  platform: "node",
  format: "esm",
  outfile: path.join(__dirname, "dist", "index.js"),
  target: "node20",
  // vm モジュールは Node.js 組み込みのため external に
  external: ["vm"],
  banner: {
    // ESM bundle 内で __dirname / __filename / require を使用可能にするための shim
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
  console.log("Build complete: dist/index.js");
}
