/**
 * Hydra 式 pruning モジュールの public API。
 * PR #1 では AST 差分判定 (SubtreeDiff / parse) と型のみ公開。
 * pruning engine 本体 (prune / prune-batch) は PR #2 で追加予定。
 */
export { parse } from "./ast/parser";
export { SubtreeDiff } from "./ast/diff";
export type {
  Placeholder,
  PlaceholderKind,
  PruningInput,
  PruningResult,
  PruningVerdict,
} from "../shared/types";
