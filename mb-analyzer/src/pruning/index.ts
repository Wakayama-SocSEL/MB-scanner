/** Pruning モジュールの public API。 */
export { parse } from "./ast/parser";
export { SubtreeDiff } from "./ast/diff";
export { prune } from "./engine";
export type {
  Placeholder,
  PlaceholderKind,
  PruningInput,
  PruningResult,
  PruningVerdict,
} from "../shared/types";
