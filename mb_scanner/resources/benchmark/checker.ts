/**
 * checker.ts
 *
 * slow/fast コードの等価性チェックを行うモジュール。
 */

import { stdoutStrategy } from "./strategies/stdout";
import { functionsStrategy } from "./strategies/functions";
import { variablesStrategy } from "./strategies/variables";
import type { CheckResult, CompareResult, CompareStatus, Strategy } from "./types";

function determineOverallStatus(results: CompareResult[]): CompareStatus | "skipped" {
  if (results.length === 0) return "error";
  const statuses = results.map((r) => r.status);
  if (statuses.every((s) => s === "equal")) return "equal";
  if (statuses.some((s) => s === "not_equal")) return "not_equal";
  return "error";
}

function selectStrategies(slowCode: string, fastCode: string): Strategy[] {
  if (stdoutStrategy.canApply(slowCode, fastCode)) {
    return [stdoutStrategy];
  }
  return [functionsStrategy, variablesStrategy].filter((s) =>
    s.canApply(slowCode, fastCode)
  );
}

function filterAndLogResults(results: CompareResult[]): CompareResult[] {
  const filtered: CompareResult[] = [];
  for (const result of results) {
    if (result.status === "equal") {
      process.stderr.write(
        `[equal] ${result.comparison_method} slow=${result.slow_output} fast=${result.fast_output}\n`
      );
    } else {
      filtered.push(result);
    }
  }
  return filtered;
}

export function check(slowCode: string, fastCode: string, timeoutMs: number): CheckResult {
  const strategies = selectStrategies(slowCode, fastCode);

  if (strategies.length === 0) {
    return {
      status: "skipped",
      strategy_results: [],
      error_message: "No applicable comparison strategy found",
    };
  }

  const allResults = strategies.map((s) => s.compare(slowCode, fastCode, timeoutMs));
  const filteredResults = filterAndLogResults(allResults);

  return {
    status: determineOverallStatus(allResults),
    strategy_results: filteredResults,
  };
}
