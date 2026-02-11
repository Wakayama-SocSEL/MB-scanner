/**
 * functions.js
 *
 * 戦略2: FUNCTION_* の戻り値を比較する戦略。
 * 関数が定義され呼び出されているが、戻り値が変数に代入されていないケースを検出し、
 * 戻り値をキャプチャして比較する。
 */

const { executeCode } = require("../sandbox");

/**
 * コードから FUNCTION_* の関数定義名を抽出する
 * @param {string} code - JavaScript ソースコード
 * @returns {string[]} 関数名の配列
 */
function extractFunctionDeclarations(code) {
  const funcPattern = /\bfunction\s+(FUNCTION_\w+)\s*\(/g;
  const funcs = new Set();
  let match;
  while ((match = funcPattern.exec(code)) !== null) {
    funcs.add(match[1]);
  }
  return Array.from(funcs);
}

/**
 * コードから FUNCTION_* の呼び出し文（戻り値が変数に代入されていないもの）を抽出する
 * @param {string} code - JavaScript ソースコード
 * @param {string[]} funcNames - 対象の関数名
 * @returns {string[]} 呼び出し式の配列（例: "FUNCTION_1(VAR_1)"）
 */
function extractUnassignedCalls(code, funcNames) {
  const calls = [];
  for (const name of funcNames) {
    // 行頭（スペース含む）で関数呼び出しが始まるパターン（変数代入なし）
    // "FUNCTION_1(args);" のような文を検出する
    // "var x = FUNCTION_1(args);" や "x = FUNCTION_1(args);" は除外
    const callPattern = new RegExp(
      `^\\s*${name}\\s*\\(([^)]*)\\)\\s*;?\\s*$`,
      "gm"
    );
    let match;
    while ((match = callPattern.exec(code)) !== null) {
      // マッチした行全体をトリムして取得
      const callExpr = match[0].trim().replace(/;$/, "");
      calls.push(callExpr);
    }
  }
  return calls;
}

/**
 * この戦略が適用可能かを判定する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @returns {boolean}
 */
function canApply(slowCode, fastCode) {
  const slowFuncs = extractFunctionDeclarations(slowCode);
  const fastFuncs = extractFunctionDeclarations(fastCode);

  if (slowFuncs.length === 0 && fastFuncs.length === 0) {
    return false;
  }

  const slowCalls = extractUnassignedCalls(slowCode, slowFuncs);
  const fastCalls = extractUnassignedCalls(fastCode, fastFuncs);

  return slowCalls.length > 0 || fastCalls.length > 0;
}

/**
 * 関数呼び出しの戻り値をキャプチャするコードを生成して実行する
 * @param {string} code - 元の JavaScript コード
 * @param {string[]} funcNames - 関数名の配列
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ output: string, error: string | null }}
 */
function executeWithFunctionCapture(code, funcNames, timeoutMs) {
  const calls = extractUnassignedCalls(code, funcNames);
  if (calls.length === 0) {
    return { output: "", error: null };
  }

  // 各呼び出し文を console.log(JSON.stringify(...)) に置き換える
  let modifiedCode = code;
  for (const callExpr of calls) {
    modifiedCode = modifiedCode.replace(
      callExpr,
      `console.log(JSON.stringify(${callExpr}))`
    );
  }

  return executeCode(modifiedCode, timeoutMs);
}

/**
 * FUNCTION_* の戻り値を比較する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ status: string, comparison_method: string, slow_output: string|null, fast_output: string|null, error_message: string|null }}
 */
function compare(slowCode, fastCode, timeoutMs) {
  const slowFuncs = extractFunctionDeclarations(slowCode);
  const fastFuncs = extractFunctionDeclarations(fastCode);

  const slowResult = executeWithFunctionCapture(slowCode, slowFuncs, timeoutMs);
  const fastResult = executeWithFunctionCapture(fastCode, fastFuncs, timeoutMs);

  if (slowResult.error || fastResult.error) {
    return {
      status: "error",
      comparison_method: "functions",
      slow_output: slowResult.output || null,
      fast_output: fastResult.output || null,
      error_message: slowResult.error || fastResult.error,
    };
  }

  return {
    status: slowResult.output === fastResult.output ? "equal" : "not_equal",
    comparison_method: "functions",
    slow_output: slowResult.output,
    fast_output: fastResult.output,
    error_message: null,
  };
}

module.exports = { canApply, compare };
