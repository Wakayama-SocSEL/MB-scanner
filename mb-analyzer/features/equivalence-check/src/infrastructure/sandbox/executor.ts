/**
 * executor.ts
 *
 * サンドボックス環境でJavaScriptコードを実行する共通モジュール。
 */

import vm from "vm";
import { createStabilizedMath, createStabilizedDate } from "./stabilizer";
import type { ExecuteResult } from "../../domain/types";

type ConsoleLike = {
  log: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
  dir: (...args: unknown[]) => void;
};

type Sandbox = {
  console: ConsoleLike;
  setTimeout: () => void;
  setInterval: () => void;
  clearTimeout: () => void;
  clearInterval: () => void;
  Math: Math;
  JSON: typeof JSON;
  parseInt: typeof parseInt;
  parseFloat: typeof parseFloat;
  isNaN: typeof isNaN;
  isFinite: typeof isFinite;
  Number: typeof Number;
  String: typeof String;
  Boolean: typeof Boolean;
  Array: typeof Array;
  Object: typeof Object;
  Date: unknown;
  RegExp: typeof RegExp;
  Error: typeof Error;
  TypeError: typeof TypeError;
  RangeError: typeof RangeError;
  Map: typeof Map;
  Set: typeof Set;
  Promise: typeof Promise;
  Symbol: typeof Symbol;
  undefined: undefined;
  NaN: number;
  Infinity: number;
};

function createSandbox(logFn: (...args: unknown[]) => void): Sandbox {
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
    JSON,
    parseInt,
    parseFloat,
    isNaN,
    isFinite,
    Number,
    String,
    Boolean,
    Array,
    Object,
    Date: createStabilizedDate(),
    RegExp,
    Error,
    TypeError,
    RangeError,
    Map,
    Set,
    Promise,
    Symbol,
    undefined,
    NaN,
    Infinity,
  };
}

export function executeCode(code: string, timeoutMs: number): ExecuteResult {
  const outputs: string[] = [];
  const sandbox = createSandbox((...args: unknown[]) => {
    outputs.push(args.map(String).join(" "));
  });

  try {
    const context = vm.createContext(sandbox);
    vm.runInContext(code, context, { timeout: timeoutMs });
    return { output: outputs.join("\n"), error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { output: outputs.join("\n"), error: message };
  }
}
