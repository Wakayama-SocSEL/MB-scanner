import type { File, Node } from "@babel/types";

import { checkEquivalence } from "../equivalence-checker";
import {
  PRUNING_VERDICT,
  VERDICT,
  type Placeholder,
  type PruningInput,
  type PruningResult,
} from "../shared/types";

import { SubtreeDiff } from "./ast/diff";
import { countNodes, snippetOfNode } from "./ast/inspect";
import { generate, parse } from "./ast/parser";
import { enumerateCandidates, type CandidatePath } from "./candidates";
import { replacementFor } from "./rules/replacement";

/**
 * Hydra 式実行ベース pruning の本体。
 *
 * 処理の骨格 (研究計画 ai-guide/current-research.md §第 1 段階):
 *
 *   1. 初回等価性検証: slow ≡ fast が `setup` 上で成立しなければ `initial_mismatch`
 *      (pruning 前提が崩れているので即 return)
 *   2. AST 差分フィルタ: SubtreeDiff で fast に同型が存在する「共通ノード」のみを
 *      候補として列挙。差分ノードは「fast に対応物がない = パターンの本質」として
 *      必須扱い (試行しない)
 *   3. 候補を大きい順に DFS 走査: 1 候補ごとに親キーを mutate → 等価判定 → 等価なら
 *      reparsed AST を採用、不等価/round-trip 失敗なら finally で必ず revert (DB の
 *      savepoint パターン)。pruning は単スレッド逐次なので isolation 不要が成立
 *   4. budget (max_iterations / total_budget_ms) で打ち切り
 *
 * 単一 setup 設計の採用判断は ai-guide/adr/0004-pruning-setup-single.md 参照。
 */

interface ResolvedConfig {
  readonly setup: string;
  readonly fastCode: string;
  readonly timeout_ms: number;
  readonly max_iterations: number;
  readonly total_budget_ms: number;
}

const DEFAULT_TIMEOUT_MS = 5_000;
const DEFAULT_MAX_ITERATIONS = 1_000;

/**
 * 1 回の checkEquivalence 呼び出しを最大 timeout_ms 使う前提で、
 * max_iterations 分の予算と等しいだけの wall-time を確保する。
 */
function resolveBudget(input: PruningInput): ResolvedConfig {
  const timeout_ms = input.timeout_ms ?? DEFAULT_TIMEOUT_MS;
  const max_iterations = input.max_iterations ?? DEFAULT_MAX_ITERATIONS;
  return {
    setup: input.setup ?? "",
    fastCode: input.fast,
    timeout_ms,
    max_iterations,
    total_budget_ms: timeout_ms * max_iterations,
  };
}

/**
 * `prune` の本体。失敗時は verdict=error を返し例外は呼び出し側へ投げない。
 */
export async function prune(input: PruningInput): Promise<PruningResult> {
  const cfg = resolveBudget(input);
  const baseResult = {
    ...(input.id !== undefined ? { id: input.id } : {}),
    effective_timeout_ms: cfg.timeout_ms,
  };

  // Phase 0: parse。parse 失敗は verdict=error。
  let slowAst: File;
  let fastAst: File;
  let currentSlowCode: string;
  try {
    slowAst = parse(input.slow);
    fastAst = parse(input.fast);
    currentSlowCode = input.slow;
  } catch (e) {
    const message = e instanceof Error ? e.message : "parse failed";
    return {
      ...baseResult,
      verdict: PRUNING_VERDICT.ERROR,
      error_message: message,
    };
  }

  const nodeCountBefore = countNodes(slowAst);

  // Phase 1: 初回等価性検証。slow ≡ fast でなければ pruning を回す意味がない。
  const initialCheck = await checkEquivalence({
    setup: cfg.setup,
    slow: currentSlowCode,
    fast: cfg.fastCode,
    timeout_ms: cfg.timeout_ms,
  });
  if (initialCheck.verdict === VERDICT.ERROR) {
    return {
      ...baseResult,
      verdict: PRUNING_VERDICT.ERROR,
      error_message: initialCheck.error_message ?? "initial equivalence check error",
      node_count_before: nodeCountBefore,
    };
  }
  if (initialCheck.verdict !== VERDICT.EQUAL) {
    return {
      ...baseResult,
      verdict: PRUNING_VERDICT.INITIAL_MISMATCH,
      node_count_before: nodeCountBefore,
    };
  }

  // Phase 2: AST 差分フィルタ + 候補列挙 + DFS 走査
  // 1 回 prune に成功したら AST が変わるので候補を再列挙する。再列挙のたびに
  // SubtreeDiff も計算し直す。失敗候補のクロスパス dedup は将来の最適化として保留
  // (canonical hash ベースで実装する余地あり)。
  const placeholders: Placeholder[] = [];
  let iterations = 0;
  const startedAt = Date.now();

  while (iterations < cfg.max_iterations) {
    if (Date.now() - startedAt >= cfg.total_budget_ms) break;

    const diff = new SubtreeDiff(slowAst, fastAst);
    const candidates = enumerateCandidates(slowAst, diff);
    if (candidates.length === 0) break;

    const prunedInThisPass = await tryPruneCandidates({
      candidates,
      slowAst,
      currentSlowCode,
      cfg,
      placeholders,
      startedAt,
      iterations,
    });

    iterations = prunedInThisPass.iterations;
    if (!prunedInThisPass.pruned) break; // もう縮まない or budget 切れ

    slowAst = prunedInThisPass.nextAst;
    currentSlowCode = prunedInThisPass.nextCode;
  }

  const patternCode = generate(slowAst);
  const nodeCountAfter = countNodes(slowAst);

  return {
    ...baseResult,
    verdict: PRUNING_VERDICT.PRUNED,
    pattern_ast: slowAst,
    pattern_code: patternCode,
    placeholders,
    iterations,
    node_count_before: nodeCountBefore,
    node_count_after: nodeCountAfter,
  };
}

interface TryPruneInput {
  readonly candidates: CandidatePath[];
  readonly slowAst: File;
  readonly currentSlowCode: string;
  readonly cfg: ResolvedConfig;
  readonly placeholders: Placeholder[];
  readonly startedAt: number;
  readonly iterations: number;
}

interface TryPruneResult {
  readonly pruned: boolean;
  readonly nextAst: File;
  readonly nextCode: string;
  readonly iterations: number;
}

/**
 * 現在の候補リストを順に試し、最初に成功した 1 候補で AST を更新して返す。
 * 各候補は親キーを mutate → 等価判定 → finally で必ず revert (savepoint パターン)。
 * 全候補が失敗、または budget 切れの場合は `pruned=false` を返し、`iterations` は
 * 試行で消費した分まで反映済み。
 */
async function tryPruneCandidates(args: TryPruneInput): Promise<TryPruneResult> {
  const { candidates, slowAst, currentSlowCode, cfg, placeholders, startedAt } = args;
  let iterations = args.iterations;
  const stop = (): TryPruneResult => ({
    pruned: false,
    nextAst: slowAst,
    nextCode: currentSlowCode,
    iterations,
  });

  for (const candidate of candidates) {
    if (iterations >= cfg.max_iterations) return stop();
    if (Date.now() - startedAt >= cfg.total_budget_ms) return stop();

    const replacement = replacementFor(candidate.node);
    if (replacement === null) continue; // whitelist 外 (通常 enumerateCandidates で弾かれる)

    const placeholderId = `$P${placeholders.length}`;
    const saved = readAt(candidate.parent, candidate.parentKey, candidate.listIndex);
    if (!applyAt(candidate.parent, candidate.parentKey, candidate.listIndex, replacement.buildNode(placeholderId))) {
      continue;
    }

    let succeeded = false;
    try {
      let code: string;
      let reparsed: File;
      try {
        code = generate(slowAst);
        reparsed = parse(code);
      } catch {
        continue; // round-trip 失敗 (finally で revert)
      }

      iterations += 1;
      const result = await checkEquivalence({
        setup: cfg.setup,
        slow: code,
        fast: cfg.fastCode,
        timeout_ms: cfg.timeout_ms,
      });

      if (result.verdict !== VERDICT.EQUAL) continue; // 不等価 / error → 次候補へ

      succeeded = true;
      placeholders.push({
        id: placeholderId,
        kind: replacement.placeholderKind,
        original_snippet: snippetOfNode(candidate.node, currentSlowCode),
      });
      return {
        pruned: true,
        nextAst: reparsed,
        nextCode: code,
        iterations,
      };
    } finally {
      if (!succeeded) applyAt(candidate.parent, candidate.parentKey, candidate.listIndex, saved);
    }
  }

  return stop();
}

function readAt(parent: Node, parentKey: string, listIndex: number | undefined): unknown {
  const record = parent as unknown as Record<string, unknown>;
  if (listIndex === undefined) return record[parentKey];
  const arr = record[parentKey];
  return Array.isArray(arr) ? (arr as unknown[])[listIndex] : undefined;
}

function applyAt(
  parent: Node,
  parentKey: string,
  listIndex: number | undefined,
  value: unknown,
): boolean {
  const record = parent as unknown as Record<string, unknown>;
  if (listIndex === undefined) {
    record[parentKey] = value;
    return true;
  }
  const arr = record[parentKey];
  if (!Array.isArray(arr)) return false;
  if (listIndex < 0 || listIndex >= arr.length) return false;
  (arr as unknown[])[listIndex] = value;
  return true;
}
