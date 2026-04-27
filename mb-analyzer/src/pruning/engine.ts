import generateModule from "@babel/generator";
import type { File, Node } from "@babel/types";

import { checkEquivalence } from "../equivalence-checker";
import {
  PLACEHOLDER_KIND,
  PRUNING_VERDICT,
  VERDICT,
  type Placeholder,
  type PlaceholderKind,
  type PruningInput,
  type PruningResult,
} from "../shared/types";

import { enumerateCandidates, type CandidatePath } from "./ast/candidates";
import { SubtreeDiff } from "./ast/diff";
import { parse } from "./ast/parser";
import { replaceNode, type ReplacementMode } from "./ast/replace";
import { NODE_CATEGORY, type NodeCategory } from "./constants";

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
 *   3. 候補を大きい順に DFS 走査: 1 箇所置換 → checkEquivalence → 等価なら AST 更新
 *      (ワイルドカード化) して次の候補へ; 非等価/error なら必須として残す
 *   4. budget (max_iterations / total_budget_ms) で打ち切り
 *
 * 単一 setup 設計の採用判断は ai-guide/adr/0004-pruning-setup-single.md 参照。
 */

/**
 * pruning の拡張入力。public API (`prune`) は `PruningInput` だけを受け取り、
 * wall-time 上限などの詳細はここで内部的に解決する。
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
 * NodeCategory と置換モードの対応。
 *
 * 大は小を兼ねない (Statement を identifier wildcard で置換すると AST 型不整合で
 * round-trip 失敗) ので、カテゴリごとに意味のあるモードだけを選ぶ。カテゴリ自体の
 * 定義は constants.ts 側の NODE_CATEGORY に集約。
 */
const MODE_BY_CATEGORY: Record<NodeCategory, ReplacementMode> = {
  statement: "deleteStatement",
  identifier: "wildcardIdentifier",
  expression: "wildcardExpression",
};

function modesForNode(node: Node): ReplacementMode[] {
  const category = NODE_CATEGORY.get(node.type);
  if (category === undefined) return [];
  return [MODE_BY_CATEGORY[category]];
}

function placeholderKindForMode(mode: ReplacementMode): PlaceholderKind {
  switch (mode) {
    case "deleteStatement":
      return PLACEHOLDER_KIND.STATEMENT;
    case "wildcardIdentifier":
      return PLACEHOLDER_KIND.IDENTIFIER;
    case "wildcardExpression":
      return PLACEHOLDER_KIND.EXPRESSION;
  }
}

/**
 * 候補ノードの元スニペットを再構成する。start/end が取れれば元コードから切り出し、
 * 取れなければ generate で近似。第 2 段階で参照するのは「何を置換したか」の情報。
 */
function snippetOfNode(node: Node, sourceCode: string): string {
  const start = node.start;
  const end = node.end;
  if (typeof start === "number" && typeof end === "number" && end >= start) {
    return sourceCode.slice(start, end);
  }
  const generator = (generateModule as unknown as { default?: typeof generateModule })
    .default ?? generateModule;
  try {
    return generator(node).code;
  } catch {
    return "";
  }
}

function generateCode(file: File): string {
  const generator = (generateModule as unknown as { default?: typeof generateModule })
    .default ?? generateModule;
  return generator(file).code;
}

function countNodes(file: File): number {
  let count = 0;
  function walk(node: unknown): void {
    if (node === null || node === undefined) return;
    if (Array.isArray(node)) {
      for (const n of node as unknown[]) walk(n);
      return;
    }
    if (typeof node !== "object") return;
    const obj = node as { type?: unknown };
    if (typeof obj.type !== "string") return;
    count += 1;
    for (const [, v] of Object.entries(node as Record<string, unknown>)) {
      if (v !== null && typeof v === "object") walk(v);
    }
  }
  walk(file);
  return count;
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
  const placeholders: Placeholder[] = [];
  let iterations = 0;
  const startedAt = Date.now();

  // 非等価/error 判定が出たノード (必須扱い) を記録。再列挙で同じ位置を
  // 再度試さないよう、canonicalHash ではなく参照同一性で素通しする。
  const essentialNodes = new WeakSet<Node>();

  // 1 回 prune に成功したら候補は再列挙する (AST 構造が変わっているため)。
  // ただし必須と判定された候補は同一 AST 上で再試行しないので、essentialNodes で除外。
  while (iterations < cfg.max_iterations) {
    if (Date.now() - startedAt >= cfg.total_budget_ms) break;

    const diff = new SubtreeDiff(slowAst, fastAst);
    const candidates = enumerateCandidates(slowAst, diff).filter(
      (c) => !essentialNodes.has(c.node),
    );
    if (candidates.length === 0) break;

    const prunedInThisPass = await tryPruneCandidates({
      candidates,
      slowAst,
      currentSlowCode,
      cfg,
      essentialNodes,
      placeholders,
      startedAt,
      iterationsRef: { value: iterations },
    });

    if (prunedInThisPass === null) break; // budget 切れ
    iterations = prunedInThisPass.iterations;
    if (!prunedInThisPass.pruned) break; // もう縮まない

    slowAst = prunedInThisPass.nextAst;
    currentSlowCode = prunedInThisPass.nextCode;
  }

  const patternCode = generateCode(slowAst);
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

interface IterationsRef {
  value: number;
}

interface TryPruneInput {
  readonly candidates: CandidatePath[];
  readonly slowAst: File;
  readonly currentSlowCode: string;
  readonly cfg: ResolvedConfig;
  readonly essentialNodes: WeakSet<Node>;
  readonly placeholders: Placeholder[];
  readonly startedAt: number;
  readonly iterationsRef: IterationsRef;
}

interface TryPruneResult {
  readonly pruned: boolean;
  readonly nextAst: File;
  readonly nextCode: string;
  readonly iterations: number;
}

/**
 * 現在の候補リストを順に試し、最初に成功した 1 候補で AST を更新して返す。
 * どの候補も成功しなければ `pruned=false`。budget 切れは null を返す。
 */
async function tryPruneCandidates(args: TryPruneInput): Promise<TryPruneResult | null> {
  const { candidates, slowAst, currentSlowCode, cfg, essentialNodes, placeholders, startedAt, iterationsRef } =
    args;

  for (const candidate of candidates) {
    if (iterationsRef.value >= cfg.max_iterations) return null;
    if (Date.now() - startedAt >= cfg.total_budget_ms) return null;

    const modes = modesForNode(candidate.node);
    let pruned = false;
    let nextAst: File = slowAst;
    let nextCode = currentSlowCode;

    for (const mode of modes) {
      if (iterationsRef.value >= cfg.max_iterations) return null;
      if (Date.now() - startedAt >= cfg.total_budget_ms) return null;

      const placeholderId = `$P${placeholders.length}`;
      const replaced = replaceNode({
        file: slowAst,
        parent: candidate.parent,
        parentKey: candidate.parentKey,
        ...(candidate.listIndex !== undefined ? { listIndex: candidate.listIndex } : {}),
        mode,
        placeholderId,
      });
      if (replaced === null) continue; // round-trip 失敗 → 次モード / 次候補

      iterationsRef.value += 1;
      const result = await checkEquivalence({
        setup: cfg.setup,
        slow: replaced.code,
        fast: cfg.fastCode,
        timeout_ms: cfg.timeout_ms,
      });

      if (result.verdict === VERDICT.EQUAL) {
        placeholders.push({
          id: placeholderId,
          kind: placeholderKindForMode(mode),
          original_snippet: snippetOfNode(candidate.node, currentSlowCode),
        });
        nextAst = replaced.file;
        nextCode = replaced.code;
        pruned = true;
        break;
      }
    }

    if (pruned) {
      return { pruned: true, nextAst, nextCode, iterations: iterationsRef.value };
    }
    // この候補はどのモードでも prune できなかった → 必須扱い
    essentialNodes.add(candidate.node);
  }

  return { pruned: false, nextAst: slowAst, nextCode: currentSlowCode, iterations: iterationsRef.value };
}
