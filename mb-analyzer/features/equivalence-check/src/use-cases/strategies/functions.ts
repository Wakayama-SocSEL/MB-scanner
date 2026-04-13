/**
 * functions.ts
 *
 * 戦略2: FUNCTION_* の戻り値を比較する戦略。
 */

import { executeCode } from "../../infrastructure/sandbox/executor";
import type { CompareResult, ExecuteResult, Strategy } from "../../domain/types";

function extractFunctionDeclarations(code: string): string[] {
  const funcPattern = /\bfunction\s+(FUNCTION_\w+)\s*\(/g;
  const funcs = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = funcPattern.exec(code)) !== null) {
    funcs.add(match[1]);
  }
  return Array.from(funcs);
}

function extractUnassignedCalls(code: string, funcNames: string[]): string[] {
  const calls: string[] = [];
  for (const name of funcNames) {
    const callPattern = new RegExp(
      `^\\s*${name}\\s*\\(([^)]*)\\)\\s*;?\\s*$`,
      "gm"
    );
    let match: RegExpExecArray | null;
    while ((match = callPattern.exec(code)) !== null) {
      const callExpr = match[0].trim().replace(/;$/, "");
      calls.push(callExpr);
    }
  }
  return calls;
}

function canApply(slowCode: string, fastCode: string): boolean {
  const slowFuncs = extractFunctionDeclarations(slowCode);
  const fastFuncs = extractFunctionDeclarations(fastCode);

  if (slowFuncs.length === 0 && fastFuncs.length === 0) {
    return false;
  }

  const slowCalls = extractUnassignedCalls(slowCode, slowFuncs);
  const fastCalls = extractUnassignedCalls(fastCode, fastFuncs);

  return slowCalls.length > 0 || fastCalls.length > 0;
}

function executeWithFunctionCapture(
  code: string,
  funcNames: string[],
  timeoutMs: number
): ExecuteResult {
  const calls = extractUnassignedCalls(code, funcNames);
  if (calls.length === 0) {
    return { output: "", error: null };
  }

  let modifiedCode = code;
  for (const callExpr of calls) {
    modifiedCode = modifiedCode.replace(
      callExpr,
      `console.log(JSON.stringify(${callExpr}))`
    );
  }

  return executeCode(modifiedCode, timeoutMs);
}

function compare(slowCode: string, fastCode: string, timeoutMs: number): CompareResult {
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

export const functionsStrategy: Strategy = { canApply, compare };
