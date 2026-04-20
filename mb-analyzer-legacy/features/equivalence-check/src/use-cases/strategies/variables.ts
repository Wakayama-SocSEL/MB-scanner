/**
 * variables.ts
 *
 * 戦略3: VAR_* 変数の最終状態を比較する戦略。
 */

import { executeCode } from "../../infrastructure/sandbox/executor";
import type { CompareResult, ExecuteResult, Strategy } from "../../domain/types";

function extractVarDeclarations(code: string): string[] {
  const varPattern = /\bvar\s+(VAR_\w+)/g;
  const vars = new Set<string>();
  let match: RegExpExecArray | null;
  while ((match = varPattern.exec(code)) !== null) {
    vars.add(match[1]);
  }
  return Array.from(vars);
}

function canApply(slowCode: string, fastCode: string): boolean {
  const slowVars = extractVarDeclarations(slowCode);
  const fastVars = extractVarDeclarations(fastCode);
  return slowVars.length > 0 || fastVars.length > 0;
}

function executeWithVarDump(code: string, varNames: string[], timeoutMs: number): ExecuteResult {
  if (varNames.length === 0) {
    return { output: "", error: null };
  }
  const dumpCode = code + "\n" + `console.log(JSON.stringify({${varNames.join(",")}}));\n`;
  return executeCode(dumpCode, timeoutMs);
}

function compare(slowCode: string, fastCode: string, timeoutMs: number): CompareResult {
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

export const variablesStrategy: Strategy = { canApply, compare };
