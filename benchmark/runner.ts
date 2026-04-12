/**
 * runner.ts
 *
 * slow.js と fast.js を受け取り、等価性チェックの結果を JSON で出力するエントリポイント。
 *
 * 引数: slow.js のパス, fast.js のパス, [timeout_ms]
 * 出力: JSON形式の比較結果を stdout に出力
 */

import fs from "fs";
import path from "path";
import { check } from "./checker";

const slowPath = process.argv[2];
const fastPath = process.argv[3];
const timeoutMs = parseInt(process.argv[4], 10) || 100000;

if (!slowPath || !fastPath) {
  console.error("Usage: node runner.js <slow.js> <fast.js> [timeout_ms]");
  process.exit(1);
}

try {
  const slowCode = fs.readFileSync(path.resolve(slowPath), "utf-8");
  const fastCode = fs.readFileSync(path.resolve(fastPath), "utf-8");
  const result = check(slowCode, fastCode, timeoutMs);
  console.log(JSON.stringify(result));
} catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  console.log(
    JSON.stringify({
      status: "error",
      strategy_results: [],
      error_message: message,
    })
  );
}
