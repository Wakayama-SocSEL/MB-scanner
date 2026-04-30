/**
 * 対象: src/pruning/rules/replacement.ts (NodeCategory → placeholderKind + buildNode dispatch)
 *
 * 観点:
 *   - replacementFor が 3 カテゴリそれぞれで正しい placeholderKind を返す
 *   - whitelist 外の型 (NODE_CATEGORY に無い) は null を返す
 *   - buildNode が各カテゴリで適切な置換ノードを生成する
 *   - identifier の placeholderId が無効な場合に sanitize される
 */
import * as t from "@babel/types";
import { describe, expect, it } from "vitest";

import { replacementFor } from "../../../src/pruning/rules/replacement";
import { PLACEHOLDER_KIND } from "../../../src/shared/types";

describe("replacementFor — placeholderKind", () => {
  it("statement カテゴリ: STATEMENT", () => {
    const node = t.ifStatement(t.identifier("c"), t.blockStatement([]));
    expect(replacementFor(node)?.placeholderKind).toBe(PLACEHOLDER_KIND.STATEMENT);
  });

  it("identifier カテゴリ: IDENTIFIER", () => {
    expect(replacementFor(t.identifier("foo"))?.placeholderKind).toBe(PLACEHOLDER_KIND.IDENTIFIER);
  });

  it("expression カテゴリ (literal): EXPRESSION", () => {
    expect(replacementFor(t.numericLiteral(42))?.placeholderKind).toBe(PLACEHOLDER_KIND.EXPRESSION);
  });

  it("expression カテゴリ (composite): EXPRESSION", () => {
    expect(
      replacementFor(t.callExpression(t.identifier("f"), []))?.placeholderKind,
    ).toBe(PLACEHOLDER_KIND.EXPRESSION);
  });

  it("whitelist 外の型 (VariableDeclarator) は null", () => {
    expect(replacementFor(t.variableDeclarator(t.identifier("x"), t.numericLiteral(1)))).toBeNull();
  });

  it("whitelist 外の型 (Program) は null", () => {
    expect(replacementFor(t.program([]))).toBeNull();
  });

  it("EmptyStatement は除外されるので null (アルゴリズム不変条件: 置換ターゲット自身)", () => {
    expect(replacementFor(t.emptyStatement())).toBeNull();
  });
});

describe("replacementFor — buildNode", () => {
  it("statement: EmptyStatement を生成", () => {
    const r = replacementFor(t.ifStatement(t.identifier("c"), t.blockStatement([])));
    const node = r!.buildNode("$P0");
    expect(node.type).toBe("EmptyStatement");
  });

  it("identifier: Identifier を生成 (placeholderId が name)", () => {
    const r = replacementFor(t.identifier("foo"));
    const node = r!.buildNode("$VAR") as t.Identifier;
    expect(node.type).toBe("Identifier");
    expect(node.name).toBe("$VAR");
  });

  it("identifier: 先頭数字の placeholderId は _ プレフィックスでサニタイズ", () => {
    const r = replacementFor(t.identifier("foo"));
    const node = r!.buildNode("123bad") as t.Identifier;
    expect(node.name).toBe("_123bad");
  });

  it("identifier: 不正文字を含む placeholderId は _ に置換", () => {
    const r = replacementFor(t.identifier("foo"));
    const node = r!.buildNode("a-b.c") as t.Identifier;
    expect(node.name).toBe("a_b_c");
  });

  it("expression: StringLiteral を生成 (placeholderId が value)", () => {
    const r = replacementFor(t.numericLiteral(42));
    const node = r!.buildNode("$P0") as t.StringLiteral;
    expect(node.type).toBe("StringLiteral");
    expect(node.value).toBe("$P0");
  });
});
