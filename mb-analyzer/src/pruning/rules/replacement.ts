import { emptyStatement, identifier, stringLiteral } from "@babel/types";
import type { Identifier, Node, StringLiteral } from "@babel/types";

import { PLACEHOLDER_KIND, type PlaceholderKind } from "../../shared/pruning-contracts";

import { WHITELIST_CATEGORIES, type NodeCategory } from "./whitelist";

/**
 * pruning 候補ノードに対する category dispatch の単一ソース。
 *
 * `NodeCategory` (入力分類 / whitelist) → 公開 API の `PlaceholderKind` と
 * 置換先 AST ノードを生成する `buildNode` の組を 1 行で対応付ける。
 * 新しい placeholder kind を追加する際の drift 面を 1 箇所に集約する目的。
 *
 * 判断: ai-guide/code-map.md (Pruning エンジン §置換操作の粒度)
 */
export interface CategoryReplacement {
  readonly placeholderKind: PlaceholderKind;
  readonly buildNode: (placeholderId: string) => Node;
}

const REPLACEMENTS: Record<NodeCategory, CategoryReplacement> = {
  statement: {
    placeholderKind: PLACEHOLDER_KIND.STATEMENT,
    buildNode: () => emptyStatement(),
  },
  identifier: {
    placeholderKind: PLACEHOLDER_KIND.IDENTIFIER,
    buildNode: (placeholderId) => identifier(sanitizeIdentifier(placeholderId)),
  },
  expression: {
    placeholderKind: PLACEHOLDER_KIND.EXPRESSION,
    buildNode: (placeholderId) => stringLiteral(placeholderId),
  },
};

/**
 * `node` の Babel 型から CategoryReplacement を引く。whitelist (`WHITELIST_CATEGORIES`) に無い
 * 型は候補対象外なので null。
 */
export function replacementFor(node: Node): CategoryReplacement | null {
  const category = WHITELIST_CATEGORIES.get(node.type);
  return category === undefined ? null : REPLACEMENTS[category];
}

/**
 * Babel identifier 名の制約 (英数字 + `_` + `$` のみ) を満たすよう placeholderId を
 * 正規化する。先頭は数字不可なので数字なら `_` を先頭に足す。
 */
function sanitizeIdentifier(placeholderId: string): string {
  const cleaned = placeholderId.replace(/[^A-Za-z0-9_$]/g, "_");
  if (cleaned.length === 0) return "$VAR";
  if (/^[0-9]/.test(cleaned)) return `_${cleaned}`;
  return cleaned;
}

// 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;
  const {
    blockStatement,
    callExpression,
    ifStatement,
    numericLiteral,
    program,
    variableDeclarator,
    emptyStatement: makeEmptyStatement,
    identifier: makeIdentifier,
  } = await import("@babel/types");

  describe("replacementFor (in-source) — placeholderKind", () => {
    it("statement カテゴリ: STATEMENT", () => {
      const node = ifStatement(makeIdentifier("c"), blockStatement([]));
      expect(replacementFor(node)?.placeholderKind).toBe(PLACEHOLDER_KIND.STATEMENT);
    });

    it("identifier カテゴリ: IDENTIFIER", () => {
      expect(replacementFor(makeIdentifier("foo"))?.placeholderKind).toBe(
        PLACEHOLDER_KIND.IDENTIFIER,
      );
    });

    it("expression カテゴリ (literal): EXPRESSION", () => {
      expect(replacementFor(numericLiteral(42))?.placeholderKind).toBe(
        PLACEHOLDER_KIND.EXPRESSION,
      );
    });

    it("expression カテゴリ (composite): EXPRESSION", () => {
      expect(replacementFor(callExpression(makeIdentifier("f"), []))?.placeholderKind).toBe(
        PLACEHOLDER_KIND.EXPRESSION,
      );
    });

    it("whitelist 外の型 (VariableDeclarator) は null", () => {
      expect(
        replacementFor(variableDeclarator(makeIdentifier("x"), numericLiteral(1))),
      ).toBeNull();
    });

    it("whitelist 外の型 (Program) は null", () => {
      expect(replacementFor(program([]))).toBeNull();
    });

    it("EmptyStatement は除外されるので null (アルゴリズム不変条件: 置換ターゲット自身)", () => {
      expect(replacementFor(makeEmptyStatement())).toBeNull();
    });
  });

  describe("replacementFor (in-source) — buildNode", () => {
    it("statement: EmptyStatement を生成", () => {
      const r = replacementFor(ifStatement(makeIdentifier("c"), blockStatement([])));
      const node = r!.buildNode("$P0");
      expect(node.type).toBe("EmptyStatement");
    });

    it("identifier: Identifier を生成 (placeholderId が name)", () => {
      const r = replacementFor(makeIdentifier("foo"));
      const node = r!.buildNode("$VAR") as Identifier;
      expect(node.type).toBe("Identifier");
      expect(node.name).toBe("$VAR");
    });

    it("identifier: 先頭数字の placeholderId は _ プレフィックスでサニタイズ", () => {
      const r = replacementFor(makeIdentifier("foo"));
      const node = r!.buildNode("123bad") as Identifier;
      expect(node.name).toBe("_123bad");
    });

    it("identifier: 不正文字を含む placeholderId は _ に置換", () => {
      const r = replacementFor(makeIdentifier("foo"));
      const node = r!.buildNode("a-b.c") as Identifier;
      expect(node.name).toBe("a_b_c");
    });

    it("identifier: 空文字列の placeholderId は $VAR に fallback (境界系)", () => {
      const r = replacementFor(makeIdentifier("foo"));
      const node = r!.buildNode("") as Identifier;
      expect(node.name).toBe("$VAR");
    });

    it("expression: StringLiteral を生成 (placeholderId が value)", () => {
      const r = replacementFor(numericLiteral(42));
      const node = r!.buildNode("$P0") as StringLiteral;
      expect(node.type).toBe("StringLiteral");
      expect(node.value).toBe("$P0");
    });
  });
}
