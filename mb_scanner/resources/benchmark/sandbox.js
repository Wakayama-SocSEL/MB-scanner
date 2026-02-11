/**
 * sandbox.js
 *
 * サンドボックス環境でJavaScriptコードを実行する共通モジュール。
 */

const vm = require("vm");
const { createStabilizedMath, createStabilizedDate } = require("./stabilizers");

/**
 * サンドボックスのコンテキストオブジェクトを生成する
 *
 * 非決定的な関数（Math.random, Date.now など）は安定化され、
 * 決定的な値を返すようになる。
 *
 * @param {function} logFn - console.log の呼び出し時に実行する関数
 * @returns {object} サンドボックスコンテキスト
 */
function createSandbox(logFn) {
  return {
    console: {
      log: logFn,
      error: () => {},
      warn: () => {},
      info: () => {},
      dir: () => {},
    },
    setTimeout: () => {},
    setInterval: () => {},
    clearTimeout: () => {},
    clearInterval: () => {},
    Math: createStabilizedMath(),
    JSON: JSON,
    parseInt: parseInt,
    parseFloat: parseFloat,
    isNaN: isNaN,
    isFinite: isFinite,
    Number: Number,
    String: String,
    Boolean: Boolean,
    Array: Array,
    Object: Object,
    Date: createStabilizedDate(),
    RegExp: RegExp,
    Error: Error,
    TypeError: TypeError,
    RangeError: RangeError,
    Map: Map,
    Set: Set,
    Promise: Promise,
    Symbol: Symbol,
    undefined: undefined,
    NaN: NaN,
    Infinity: Infinity,
  };
}

/**
 * サンドボックス環境でコードを実行し、stdout 出力をキャプチャする
 * @param {string} code - 実行する JavaScript コード
 * @param {number} timeoutMs - タイムアウト（ミリ秒）
 * @returns {{ output: string, error: string | null }}
 */
function executeCode(code, timeoutMs) {
  const outputs = [];
  const sandbox = createSandbox((...args) => {
    outputs.push(args.map(String).join(" "));
  });

  try {
    const context = vm.createContext(sandbox);
    vm.runInContext(code, context, { timeout: timeoutMs });
    return { output: outputs.join("\n"), error: null };
  } catch (err) {
    return { output: outputs.join("\n"), error: err.message || String(err) };
  }
}

module.exports = { createSandbox, executeCode };
