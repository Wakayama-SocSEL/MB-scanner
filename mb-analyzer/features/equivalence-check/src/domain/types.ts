export type ExecuteResult = {
  output: string;
  error: string | null;
};

export type CompareStatus = "equal" | "not_equal" | "error";

export type CompareResult = {
  status: CompareStatus;
  comparison_method: string;
  slow_output: string | null;
  fast_output: string | null;
  error_message: string | null;
};

export type CheckStatus = CompareStatus | "skipped";

export type CheckResult = {
  status: CheckStatus;
  strategy_results: CompareResult[];
  error_message?: string;
};

export interface Strategy {
  canApply(slowCode: string, fastCode: string): boolean;
  compare(slowCode: string, fastCode: string, timeoutMs: number): CompareResult;
}
