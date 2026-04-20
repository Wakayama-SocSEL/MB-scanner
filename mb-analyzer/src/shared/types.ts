/**
 * Python 側 (mb_scanner.domain.entities.equivalence) との JSON シリアライゼーション互換のため、
 * 列挙値の文字列とフィールド名の snake_case を厳密に揃える。
 */

export const VERDICT = {
  EQUAL: "equal",
  NOT_EQUAL: "not_equal",
  ERROR: "error",
} as const;
export type Verdict = (typeof VERDICT)[keyof typeof VERDICT];

export const ORACLE_VERDICT = {
  EQUAL: "equal",
  NOT_EQUAL: "not_equal",
  NOT_APPLICABLE: "not_applicable",
  ERROR: "error",
} as const;
export type OracleVerdict = (typeof ORACLE_VERDICT)[keyof typeof ORACLE_VERDICT];

export const ORACLE = {
  RETURN_VALUE: "return_value",
  ARGUMENT_MUTATION: "argument_mutation",
  EXCEPTION: "exception",
  EXTERNAL_OBSERVATION: "external_observation",
} as const;
export type Oracle = (typeof ORACLE)[keyof typeof ORACLE];

export const ALL_ORACLES: readonly Oracle[] = [
  ORACLE.RETURN_VALUE,
  ORACLE.ARGUMENT_MUTATION,
  ORACLE.EXCEPTION,
  ORACLE.EXTERNAL_OBSERVATION,
] as const;

export interface EquivalenceInput {
  id?: string;
  setup?: string;
  slow: string;
  fast: string;
  timeout_ms?: number;
}

export interface OracleObservation {
  oracle: Oracle;
  verdict: OracleVerdict;
  slow_value?: string | null;
  fast_value?: string | null;
  detail?: string | null;
}

export interface EquivalenceCheckResult {
  id?: string;
  verdict: Verdict;
  observations: OracleObservation[];
  error_message?: string | null;
  effective_timeout_ms?: number;
}
