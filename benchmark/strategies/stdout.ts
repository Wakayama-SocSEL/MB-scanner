/**
 * stdout.ts
 *
 * 戦略1: console.log の出力を比較する戦略。
 */

import { executeCode } from "../sandbox/executor";
import type { CompareResult, Strategy } from "../types";

function hasConsoleLog(code: string): boolean {
  return /console\s*\.\s*log\s*\(/.test(code);
}

function canApply(slowCode: string, fastCode: string): boolean {
  return hasConsoleLog(slowCode) && hasConsoleLog(fastCode);
}

function compare(slowCode: string, fastCode: string, timeoutMs: number): CompareResult {
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

export const stdoutStrategy: Strategy = { canApply, compare };
