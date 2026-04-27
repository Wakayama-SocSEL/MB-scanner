import { VISITOR_KEYS } from "@babel/types";
import type { File, Node } from "@babel/types";

import { NODE_CATEGORY } from "../constants";
import type { SubtreeDiff } from "./diff";
import { getGrammarBlacklist } from "./grammar-blacklist";

/**
 * pruning 対象となる候補ノードを列挙する。
 *
 * 候補フィルタは 3 段:
 *   1. 型 whitelist: pruning できる可能性のあるノード型 (NODE_CATEGORY) のみ残す
 *   2. 親子 blacklist: 親 field validator が置換後の型 (EmptyStatement / Identifier /
 *      StringLiteral) を受理しない位置を除外。ルールは `@babel/types` の文法メタ
 *      データから `grammar-blacklist.ts` で自動導出 (ADR 0005)
 *   3. SubtreeDiff.isCommon: fast に同型が存在する「共通ノード」に絞る
 *      (研究計画 §第 1 段階 で「差分ノードは必須扱い」とするため)
 *
 * 結果は `end - start` の降順でソート。サイズが大きい候補を先に試す方が、成功
 * 時に一度に縮む量が大きく、全体の試行回数が減る経験則。
 */

export interface CandidatePath {
  readonly node: Node;
  /** 親ノード (File 直下の Program の子以外は必ず存在)。 */
  readonly parent: Node;
  /** 親から見た子の位置 key (例: `"consequent"`, `"body"`)。 */
  readonly parentKey: string;
  /** 親の該当 key が配列の場合のインデックス。スカラ子なら undefined。 */
  readonly listIndex?: number;
}

/**
 * pruning 候補を列挙する。
 *
 * @param slow 対象の File AST
 * @param diff SubtreeDiff (fast との共通ノード判定)。undefined なら差分フィルタを
 *   適用せず全ての whitelist ノードを候補にする (テスト用)。
 */
export function enumerateCandidates(
  slow: File,
  diff?: SubtreeDiff,
): CandidatePath[] {
  const candidates: CandidatePath[] = [];
  const blacklist = getGrammarBlacklist();

  function visit(
    node: Node,
    parent: Node | null,
    parentKey: string | null,
    listIndex: number | undefined,
  ): void {
    if (parent !== null && parentKey !== null && isCandidate(node, parent, parentKey, diff)) {
      const entry: CandidatePath = {
        node,
        parent,
        parentKey,
        ...(listIndex !== undefined ? { listIndex } : {}),
      };
      candidates.push(entry);
    }

    const visitorKeys = VISITOR_KEYS[node.type] ?? [];
    const record = node as unknown as Record<string, unknown>;
    for (const key of visitorKeys) {
      const child = record[key];
      if (child === null || child === undefined) continue;
      if (Array.isArray(child)) {
        for (let i = 0; i < child.length; i++) {
          const c = child[i] as unknown;
          if (isNode(c)) visit(c, node, key, i);
        }
      } else if (isNode(child)) {
        visit(child, node, key, undefined);
      }
    }
  }

  visit(slow, null, null, undefined);

  // サイズ降順ソート: 大きい候補を先に試すことで早期収束を狙う。
  // start/end が未付与のノードは末尾へ送る (通常 parse 直後は必ず付く)。
  candidates.sort((a, b) => nodeSize(b.node) - nodeSize(a.node));

  return candidates;

  function isCandidate(
    node: Node,
    parent: Node,
    parentKey: string,
    diff: SubtreeDiff | undefined,
  ): boolean {
    const category = NODE_CATEGORY.get(node.type);
    if (category === undefined) return false;

    const rule = blacklist[category].get(parent.type)?.get(parentKey);
    if (rule === true) return false;
    if (rule !== undefined) {
      const parentValue = (parent as unknown as Record<string, unknown>)[rule.discriminator];
      if (rule.value.includes(parentValue)) return false;
    }

    if (diff !== undefined && !diff.isCommon(node)) return false;

    return true;
  }
}

function isNode(value: unknown): value is Node {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
}

function nodeSize(node: Node): number {
  const start = node.start ?? 0;
  const end = node.end ?? 0;
  return end - start;
}
