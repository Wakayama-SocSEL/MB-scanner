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

// ---------------------------------------------------------------------------
// Pruning (Hydra 式 AST 差分ベース pruning)
//
// Python 側 (mb_scanner.domain.entities.pruning) と JSON シリアライゼーション互換。
// 列挙値の文字列 / フィールド名の snake_case を厳密に揃える。
// ---------------------------------------------------------------------------

export const PRUNING_VERDICT = {
  PRUNED: "pruned",
  INITIAL_MISMATCH: "initial_mismatch",
  ERROR: "error",
} as const;
export type PruningVerdict = (typeof PRUNING_VERDICT)[keyof typeof PRUNING_VERDICT];

export const PLACEHOLDER_KIND = {
  EXPRESSION: "expression",
  STATEMENT: "statement",
  IDENTIFIER: "identifier",
} as const;
export type PlaceholderKind = (typeof PLACEHOLDER_KIND)[keyof typeof PLACEHOLDER_KIND];

export interface Placeholder {
  id: string;
  kind: PlaceholderKind;
  original_snippet: string;
}

export interface PruningInput {
  id?: string;
  slow: string;
  fast: string;
  setup: string;
  timeout_ms?: number;
  max_iterations?: number;
}

export interface PruningResult {
  id?: string;
  verdict: PruningVerdict;
  pattern_ast?: unknown;
  pattern_code?: string;
  placeholders?: Placeholder[];
  iterations?: number;
  node_count_before?: number;
  node_count_after?: number;
  effective_timeout_ms?: number;
  error_message?: string | null;
}
