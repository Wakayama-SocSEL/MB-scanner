/**
 * variables.js
 *
 * 戦略3: VAR_* 変数の最終状態を比較する戦略。
 */

const { executeCode } = require("../sandbox");

/**
 * コードから var VAR_* 宣言を正規表現で抽出する
 * @param {string} code - JavaScript ソースコード
 * @returns {string[]} 変数名の配列
 */
function extractVarDeclarations(code) {
  const varPattern = /\bvar\s+(VAR_\w+)/g;
  const vars = new Set();
  let match;
  while ((match = varPattern.exec(code)) !== null) {
    vars.add(match[1]);
  }
  return Array.from(vars);
}

/**
 * この戦略が適用可能かを判定する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @returns {boolean}
 */
function canApply(slowCode, fastCode) {
  const slowVars = extractVarDeclarations(slowCode);
  const fastVars = extractVarDeclarations(fastCode);
  return slowVars.length > 0 || fastVars.length > 0;
}

/**
 * 変数ダンプ用のコードを末尾に追加して実行する
 * @param {string} code - 元の JavaScript コード
 * @param {string[]} varNames - ダンプ対象の変数名
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ output: string, error: string | null }}
 */
function executeWithVarDump(code, varNames, timeoutMs) {
  if (varNames.length === 0) {
    return { output: "", error: null };
  }

  const dumpCode =
    code + "\n" + `console.log(JSON.stringify({${varNames.join(",")}}));\n`;
  return executeCode(dumpCode, timeoutMs);
}

/**
 * VAR_* 変数の最終状態を比較する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ status: string, comparison_method: string, slow_output: string|null, fast_output: string|null, error_message: string|null }}
 */
function compare(slowCode, fastCode, timeoutMs) {
  const slowVars = extractVarDeclarations(slowCode);
  const fastVars = extractVarDeclarations(fastCode);

  const slowResult = executeWithVarDump(slowCode, slowVars, timeoutMs);
  const fastResult = executeWithVarDump(fastCode, fastVars, timeoutMs);

  if (slowResult.error || fastResult.error) {
    return {
      status: "error",
      comparison_method: "variables",
      slow_output: slowResult.output || null,
      fast_output: fastResult.output || null,
      error_message: slowResult.error || fastResult.error,
    };
  }

  return {
    status: slowResult.output === fastResult.output ? "equal" : "not_equal",
    comparison_method: "variables",
    slow_output: slowResult.output,
    fast_output: fastResult.output,
    error_message: null,
  };
}

module.exports = { canApply, compare };
