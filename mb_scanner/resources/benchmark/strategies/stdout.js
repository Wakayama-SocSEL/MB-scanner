/**
 * stdout.js
 *
 * 戦略1: console.log の出力を比較する戦略。
 */

const { executeCode } = require("../sandbox");

/**
 * コードに console.log 呼び出しが含まれるかチェックする
 * @param {string} code - JavaScript ソースコード
 * @returns {boolean}
 */
function hasConsoleLog(code) {
  return /console\s*\.\s*log\s*\(/.test(code);
}

/**
 * この戦略が適用可能かを判定する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @returns {boolean}
 */
function canApply(slowCode, fastCode) {
  return hasConsoleLog(slowCode) && hasConsoleLog(fastCode);
}

/**
 * stdout 出力を比較する
 * @param {string} slowCode - slow版のソースコード
 * @param {string} fastCode - fast版のソースコード
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ status: string, comparison_method: string, slow_output: string|null, fast_output: string|null, error_message: string|null }}
 */
function compare(slowCode, fastCode, timeoutMs) {
  const slowResult = executeCode(slowCode, timeoutMs);
  const fastResult = executeCode(fastCode, timeoutMs);

  if (slowResult.error || fastResult.error) {
    return {
      status: "error",
      comparison_method: "stdout",
      slow_output: slowResult.output || null,
      fast_output: fastResult.output || null,
      error_message: slowResult.error || fastResult.error,
    };
  }

  return {
    status: slowResult.output === fastResult.output ? "equal" : "not_equal",
    comparison_method: "stdout",
    slow_output: slowResult.output,
    fast_output: fastResult.output,
    error_message: null,
  };
}

module.exports = { canApply, compare };
