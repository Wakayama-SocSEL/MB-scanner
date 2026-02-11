/**
 * runner.js
 *
 * slow.js と fast.js を実行し、出力を比較して等価性を検証するメインエントリポイント。
 * 各比較戦略を優先順位に従って適用する。
 *
 * 戦略の優先順位:
 *   1. stdout   - 両コードに console.log がある場合
 *   2. functions - FUNCTION_* の戻り値が未代入で呼び出されている場合
 *   3. variables - VAR_* 変数が宣言されている場合
 *   4. none     - いずれも該当しない場合 → skipped
 *
 * 引数: slow.js のパス, fast.js のパス, [timeout_ms]
 * 出力: JSON形式の比較結果を stdout に出力
 */

const fs = require("fs");
const path = require("path");

const stdoutStrategy = require("./strategies/stdout");
const functionsStrategy = require("./strategies/functions");
const variablesStrategy = require("./strategies/variables");

const slowPath = process.argv[2];
const fastPath = process.argv[3];
const timeoutMs = parseInt(process.argv[4], 10) || 100000;

if (!slowPath || !fastPath) {
  console.error(
    "Usage: node runner.js <slow.js> <fast.js> [timeout_ms]"
  );
  process.exit(1);
}

const strategies = [stdoutStrategy, functionsStrategy, variablesStrategy];

try {
  const slowCode = fs.readFileSync(path.resolve(slowPath), "utf-8");
  const fastCode = fs.readFileSync(path.resolve(fastPath), "utf-8");

  let matched = false;
  for (const strategy of strategies) {
    if (strategy.canApply(slowCode, fastCode)) {
      const result = strategy.compare(slowCode, fastCode, timeoutMs);
      console.log(JSON.stringify(result));
      matched = true;
      break;
    }
  }

  if (!matched) {
    // どの戦略も適用できない場合
    console.log(
      JSON.stringify({
        status: "skipped",
        comparison_method: "none",
        slow_output: null,
        fast_output: null,
        error_message: "No applicable comparison strategy found",
      })
    );
  }
} catch (err) {
  console.log(
    JSON.stringify({
      status: "error",
      comparison_method: "none",
      slow_output: null,
      fast_output: null,
      error_message: err.message || String(err),
    })
  );
}
