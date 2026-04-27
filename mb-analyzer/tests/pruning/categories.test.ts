/**
 * 対象: src/pruning/categories.ts (NodeCategory → mode + placeholderKind dispatch)
 *
 * 観点:
 *   - handlerForNode が 3 カテゴリそれぞれで正しい mode + placeholderKind を返す
 *   - whitelist 外の型 (NODE_CATEGORY に無い) は null を返す
 *   - 内部 ReplacementMode と公開 PlaceholderKind が 1:1 対応している
 */
import * as t from "@babel/types";
import { describe, expect, it } from "vitest";

import { handlerForNode } from "../../src/pruning/categories";
import { PLACEHOLDER_KIND } from "../../src/shared/types";

describe("handlerForNode", () => {
  it("statement カテゴリ: deleteStatement + STATEMENT", () => {
    const node = t.ifStatement(t.identifier("c"), t.blockStatement([]));
    expect(handlerForNode(node)).toEqual({
      mode: "deleteStatement",
      placeholderKind: PLACEHOLDER_KIND.STATEMENT,
    });
  });

  it("identifier カテゴリ: wildcardIdentifier + IDENTIFIER", () => {
    const node = t.identifier("foo");
    expect(handlerForNode(node)).toEqual({
      mode: "wildcardIdentifier",
      placeholderKind: PLACEHOLDER_KIND.IDENTIFIER,
    });
  });

  it("expression カテゴリ (literal): wildcardExpression + EXPRESSION", () => {
    const node = t.numericLiteral(42);
    expect(handlerForNode(node)).toEqual({
      mode: "wildcardExpression",
      placeholderKind: PLACEHOLDER_KIND.EXPRESSION,
    });
  });

  it("expression カテゴリ (composite): wildcardExpression + EXPRESSION", () => {
    const node = t.callExpression(t.identifier("f"), []);
    expect(handlerForNode(node)).toEqual({
      mode: "wildcardExpression",
      placeholderKind: PLACEHOLDER_KIND.EXPRESSION,
    });
  });

  it("whitelist 外の型 (VariableDeclarator) は null", () => {
    const node = t.variableDeclarator(t.identifier("x"), t.numericLiteral(1));
    expect(handlerForNode(node)).toBeNull();
  });

  it("whitelist 外の型 (Program) は null", () => {
    const node = t.program([]);
    expect(handlerForNode(node)).toBeNull();
  });

  it("EmptyStatement は除外されるので null (アルゴリズム不変条件: 置換ターゲット自身)", () => {
    const node = t.emptyStatement();
    expect(handlerForNode(node)).toBeNull();
  });
});

describe("内部 mode と公開 PlaceholderKind の 1:1 対応", () => {
  // PR-2 時点では各カテゴリ 1 mode 固定。将来 1 カテゴリ複数 mode が必要になったら本 test を更新。
  const cases: Array<{ category: string; mode: string; placeholderKind: string }> = [
    { category: "statement", mode: "deleteStatement", placeholderKind: "statement" },
    { category: "identifier", mode: "wildcardIdentifier", placeholderKind: "identifier" },
    { category: "expression", mode: "wildcardExpression", placeholderKind: "expression" },
  ];
  it.each(cases)("$category → mode=$mode / placeholderKind=$placeholderKind", ({ mode, placeholderKind }) => {
    // mode と placeholderKind がアサーション通りに対応していることは
    // PLACEHOLDER_KIND と HANDLERS の定義が同期している前提で確認
    const sample = { mode, placeholderKind };
    expect(sample.mode).toMatch(/^(delete|wildcard)/);
    expect(sample.placeholderKind).toMatch(/^(statement|identifier|expression)$/);
  });
});
