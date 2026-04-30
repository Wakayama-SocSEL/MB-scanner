/**
 * 対象: src/pruning/rules/whitelist.ts (alias-driven whitelist 構築)
 *
 * 観点 (ADR-0006 実装ステップ 4-6):
 *   - PARSER_PLUGINS: 現状 [] (素 JS) で固定
 *   - 想定カバレッジ: statement 24 / identifier 1 / expression 33 = 58 型
 *   - 構造的 no-op: TS / JSX / Flow plugin OFF 由来の型は除外される
 *   - アルゴリズム不変条件: EmptyStatement は除外される
 *   - 時点規範的除外: TC39 stage < 4 の experimental 型 10 種が除外される
 *   - 既存 (PR-1 以前) のリストは全て新リストに含まれる (互換性 fixed)
 *   - Babel メジャー追従検出: 想定外の型が現れたら snapshot diff で気づける
 */
import * as t from "@babel/types";
import { describe, expect, it } from "vitest";

import { NODE_CATEGORY, PARSER_PLUGINS } from "../../../src/pruning/rules/whitelist";

const PRE_PR2_WHITELIST: ReadonlyArray<readonly [string, "statement" | "expression" | "identifier"]> = [
  ["IfStatement", "statement"],
  ["ExpressionStatement", "statement"],
  ["VariableDeclaration", "statement"],
  ["BlockStatement", "statement"],
  ["ReturnStatement", "statement"],
  ["ThrowStatement", "statement"],
  ["Identifier", "identifier"],
  ["NumericLiteral", "expression"],
  ["StringLiteral", "expression"],
  ["BooleanLiteral", "expression"],
  ["NullLiteral", "expression"],
  ["RegExpLiteral", "expression"],
  ["TemplateLiteral", "expression"],
  ["MemberExpression", "expression"],
  ["CallExpression", "expression"],
  ["NewExpression", "expression"],
  ["BinaryExpression", "expression"],
  ["LogicalExpression", "expression"],
  ["UnaryExpression", "expression"],
  ["UpdateExpression", "expression"],
  ["AssignmentExpression", "expression"],
  ["ConditionalExpression", "expression"],
  ["ObjectExpression", "expression"],
  ["ArrayExpression", "expression"],
];

const EXPERIMENTAL_TYPES = [
  "BindExpression",
  "DoExpression",
  "RecordExpression",
  "TupleExpression",
  "ModuleExpression",
  "PipelineBareFunction",
  "PipelinePrimaryTopicReference",
  "PipelineTopicExpression",
  "TopicReference",
  "DecimalLiteral",
];

describe("PARSER_PLUGINS", () => {
  it("対象言語は素 JS (plugin 配列は空)", () => {
    expect(PARSER_PLUGINS).toEqual([]);
  });
});

describe("NODE_CATEGORY — 想定カバレッジ", () => {
  it("statement カテゴリは 24 型", () => {
    const stmt = [...NODE_CATEGORY.entries()].filter(([, v]) => v === "statement");
    expect(stmt.length).toBe(24);
  });

  it("identifier カテゴリは 1 型 (Identifier のみ)", () => {
    const id = [...NODE_CATEGORY.entries()].filter(([, v]) => v === "identifier");
    expect(id.map(([k]) => k)).toEqual(["Identifier"]);
  });

  it("expression カテゴリは 33 型", () => {
    const expr = [...NODE_CATEGORY.entries()].filter(([, v]) => v === "expression");
    expect(expr.length).toBe(33);
  });

  it("合計 58 型 (Babel 全 alias 99 のうち約 59%)", () => {
    expect(NODE_CATEGORY.size).toBe(58);
  });
});

describe("NODE_CATEGORY — 後方互換 (PR-2 以前のエントリは全て継承)", () => {
  it.each(PRE_PR2_WHITELIST)("既存型 %s は %s カテゴリで保持される", (type, category) => {
    expect(NODE_CATEGORY.get(type)).toBe(category);
  });
});

describe("NODE_CATEGORY — 構造的 no-op (parser plugin OFF 由来の除外)", () => {
  it("TS prefix 型は除外される", () => {
    const flipped = (t as unknown as { FLIPPED_ALIAS_KEYS?: Record<string, string[]> })
      .FLIPPED_ALIAS_KEYS!;
    const tsTypes = [...(flipped.Statement ?? []), ...(flipped.Expression ?? [])].filter((s) =>
      s.startsWith("TS"),
    );
    expect(tsTypes.length).toBeGreaterThan(0); // 前提検証
    for (const ts of tsTypes) {
      expect(NODE_CATEGORY.has(ts)).toBe(false);
    }
  });

  it("JSX prefix 型は除外される", () => {
    const flipped = (t as unknown as { FLIPPED_ALIAS_KEYS?: Record<string, string[]> })
      .FLIPPED_ALIAS_KEYS!;
    const jsxTypes = [...(flipped.Statement ?? []), ...(flipped.Expression ?? [])].filter((s) =>
      s.startsWith("JSX"),
    );
    for (const jsx of jsxTypes) {
      expect(NODE_CATEGORY.has(jsx)).toBe(false);
    }
  });

  it("Flow Declare prefix 型は除外される", () => {
    const flipped = (t as unknown as { FLIPPED_ALIAS_KEYS?: Record<string, string[]> })
      .FLIPPED_ALIAS_KEYS!;
    const flowTypes = (flipped.Statement ?? []).filter((s) => s.startsWith("Declare"));
    expect(flowTypes.length).toBeGreaterThan(0);
    for (const flow of flowTypes) {
      expect(NODE_CATEGORY.has(flow)).toBe(false);
    }
  });

  it("Flow 明示型 (TypeAlias / OpaqueType / InterfaceDeclaration / EnumDeclaration / TypeCastExpression) は除外される", () => {
    for (const flow of [
      "TypeAlias",
      "OpaqueType",
      "InterfaceDeclaration",
      "EnumDeclaration",
      "TypeCastExpression",
    ]) {
      expect(NODE_CATEGORY.has(flow)).toBe(false);
    }
  });
});

describe("NODE_CATEGORY — アルゴリズム不変条件", () => {
  it("EmptyStatement は除外される (deleteStatement の置換ターゲット自身)", () => {
    expect(NODE_CATEGORY.has("EmptyStatement")).toBe(false);
  });
});

describe("NODE_CATEGORY — 時点規範的除外 (TC39 stage < 4)", () => {
  it.each(EXPERIMENTAL_TYPES)("experimental 型 %s は除外される", (type) => {
    expect(NODE_CATEGORY.has(type)).toBe(false);
  });
});

describe("NODE_CATEGORY — Babel メジャー追従の検出", () => {
  /**
   * 現時点 (ADR-0006 Date: 2026-04-27, Babel 7.x) で whitelist 入りする 58 型を
   * snapshot として固定する。Babel 更新で alias 構造が変われば本テストが失敗し、
   * ADR トリガー (Babel メジャーバージョン更新で `FLIPPED_ALIAS_KEYS` 構造が変わる)
   * に従って ADR と除外集合を見直す合図となる。
   */
  it("現時点の 58 型を固定 (Babel alias 変更で fail → ADR-0006 見直し)", () => {
    const sorted = [...NODE_CATEGORY.entries()].sort(([a], [b]) => a.localeCompare(b));
    expect(sorted).toMatchInlineSnapshot(`
      [
        [
          "ArrayExpression",
          "expression",
        ],
        [
          "ArrowFunctionExpression",
          "expression",
        ],
        [
          "AssignmentExpression",
          "expression",
        ],
        [
          "AwaitExpression",
          "expression",
        ],
        [
          "BigIntLiteral",
          "expression",
        ],
        [
          "BinaryExpression",
          "expression",
        ],
        [
          "BlockStatement",
          "statement",
        ],
        [
          "BooleanLiteral",
          "expression",
        ],
        [
          "BreakStatement",
          "statement",
        ],
        [
          "CallExpression",
          "expression",
        ],
        [
          "ClassDeclaration",
          "statement",
        ],
        [
          "ClassExpression",
          "expression",
        ],
        [
          "ConditionalExpression",
          "expression",
        ],
        [
          "ContinueStatement",
          "statement",
        ],
        [
          "DebuggerStatement",
          "statement",
        ],
        [
          "DoWhileStatement",
          "statement",
        ],
        [
          "ExportAllDeclaration",
          "statement",
        ],
        [
          "ExportDefaultDeclaration",
          "statement",
        ],
        [
          "ExportNamedDeclaration",
          "statement",
        ],
        [
          "ExpressionStatement",
          "statement",
        ],
        [
          "ForInStatement",
          "statement",
        ],
        [
          "ForOfStatement",
          "statement",
        ],
        [
          "ForStatement",
          "statement",
        ],
        [
          "FunctionDeclaration",
          "statement",
        ],
        [
          "FunctionExpression",
          "expression",
        ],
        [
          "Identifier",
          "identifier",
        ],
        [
          "IfStatement",
          "statement",
        ],
        [
          "Import",
          "expression",
        ],
        [
          "ImportDeclaration",
          "statement",
        ],
        [
          "ImportExpression",
          "expression",
        ],
        [
          "LabeledStatement",
          "statement",
        ],
        [
          "LogicalExpression",
          "expression",
        ],
        [
          "MemberExpression",
          "expression",
        ],
        [
          "MetaProperty",
          "expression",
        ],
        [
          "NewExpression",
          "expression",
        ],
        [
          "NullLiteral",
          "expression",
        ],
        [
          "NumericLiteral",
          "expression",
        ],
        [
          "ObjectExpression",
          "expression",
        ],
        [
          "OptionalCallExpression",
          "expression",
        ],
        [
          "OptionalMemberExpression",
          "expression",
        ],
        [
          "ParenthesizedExpression",
          "expression",
        ],
        [
          "RegExpLiteral",
          "expression",
        ],
        [
          "ReturnStatement",
          "statement",
        ],
        [
          "SequenceExpression",
          "expression",
        ],
        [
          "StringLiteral",
          "expression",
        ],
        [
          "Super",
          "expression",
        ],
        [
          "SwitchStatement",
          "statement",
        ],
        [
          "TaggedTemplateExpression",
          "expression",
        ],
        [
          "TemplateLiteral",
          "expression",
        ],
        [
          "ThisExpression",
          "expression",
        ],
        [
          "ThrowStatement",
          "statement",
        ],
        [
          "TryStatement",
          "statement",
        ],
        [
          "UnaryExpression",
          "expression",
        ],
        [
          "UpdateExpression",
          "expression",
        ],
        [
          "VariableDeclaration",
          "statement",
        ],
        [
          "WhileStatement",
          "statement",
        ],
        [
          "WithStatement",
          "statement",
        ],
        [
          "YieldExpression",
          "expression",
        ],
      ]
    `);
  });
});
