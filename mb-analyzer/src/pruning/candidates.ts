import type { File, Node } from "@babel/types";

import type { SubtreeDiff } from "./ast/diff";
import { nodeSize } from "./ast/inspect";
import { walkNodes } from "./ast/walk";
import { getGrammarBlacklist, type ExcludeRule, type GrammarBlacklist } from "./rules/blacklist";
import { NODE_CATEGORY } from "./rules/whitelist";

/**
 * pruning 対象となる候補ノードを列挙する。
 *
 * 候補フィルタは 3 段 (`isCandidate`):
 *   1. 型 whitelist: pruning できる可能性のあるノード型 (NODE_CATEGORY) のみ残す
 *   2. 親子 blacklist: 親 field validator が置換後の型 (EmptyStatement / Identifier /
 *      StringLiteral) を受理しない位置を除外。ルールは `@babel/types` の文法メタ
 *      データから `rules/blacklist.ts` で自動導出 (ADR 0005)
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
  /** 親の該当 key が配列の場合のインデックス。単一ノードを指す key なら undefined。 */
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

  walkNodes(slow, ({ node, parent, parentKey, listIndex }) => {
    if (parent === null || parentKey === null) return;
    if (!isCandidate(node, parent, parentKey, blacklist, diff)) return;
    candidates.push({
      node,
      parent,
      parentKey,
      ...(listIndex !== undefined ? { listIndex } : {}),
    });
  });

  // サイズ降順ソート: 大きい候補を先に試すことで早期収束を狙う。
  // start/end が未付与のノードは末尾へ送る (通常 parse 直後は必ず付く)。
  candidates.sort((a, b) => nodeSize(b.node) - nodeSize(a.node));

  return candidates;
}

function isCandidate(
  node: Node,
  parent: Node,
  parentKey: string,
  blacklist: GrammarBlacklist,
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

// 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;

  const stubNode = (type: string, extra: Record<string, unknown> = {}): Node =>
    ({ type, ...extra }) as unknown as Node;

  const emptyBlacklist: GrammarBlacklist = {
    statement: new Map(),
    identifier: new Map(),
    expression: new Map(),
  };

  describe("isCandidate (in-source)", () => {
    it("whitelist 外の型は他段の状態に関わらず false", () => {
      // Program は NODE_CATEGORY に無い → blacklist / diff の中身を読まずに弾かれる
      expect(
        isCandidate(stubNode("Program"), stubNode("File"), "program", emptyBlacklist, undefined),
      ).toBe(false);
    });

    it("blacklist rule === true は無条件除外", () => {
      const blacklist: GrammarBlacklist = {
        statement: new Map([["IfStatement", new Map([["test", true as ExcludeRule]])]]),
        identifier: new Map(),
        expression: new Map(),
      };
      expect(
        isCandidate(
          stubNode("BlockStatement"),
          stubNode("IfStatement"),
          "test",
          blacklist,
          undefined,
        ),
      ).toBe(false);
    });

    it("discriminator 条件付き rule は親フィールド値で切り替わる", () => {
      const rule: ExcludeRule = { discriminator: "kind", value: ["const"] };
      const blacklist: GrammarBlacklist = {
        statement: new Map(),
        identifier: new Map([["VariableDeclarator", new Map([["id", rule]])]]),
        expression: new Map(),
      };
      const child = stubNode("Identifier");
      // kind=const → 除外
      expect(
        isCandidate(
          child,
          stubNode("VariableDeclarator", { kind: "const" }),
          "id",
          blacklist,
          undefined,
        ),
      ).toBe(false);
      // kind=let → 通過 (rule があっても discriminator が一致しない)
      expect(
        isCandidate(
          child,
          stubNode("VariableDeclarator", { kind: "let" }),
          "id",
          blacklist,
          undefined,
        ),
      ).toBe(true);
    });

    it("diff の isCommon === false は除外、undefined 時は diff 段がスキップされる", () => {
      const id = stubNode("Identifier");
      const parent = stubNode("ExpressionStatement");
      const diffReject = { isCommon: () => false } as unknown as SubtreeDiff;

      expect(isCandidate(id, parent, "expression", emptyBlacklist, diffReject)).toBe(false);
      expect(isCandidate(id, parent, "expression", emptyBlacklist, undefined)).toBe(true);
    });
  });
}
