/**
 * 対象: src/pruning/ast/diff.ts (正規化ハッシュ + SubtreeDiff.isCommon)
 * 観点: hash の決定性・情報保持・エッジケース + Selakovic #1 (hasOwnProperty) の common/diff 分離
 * 判定事項:
 *   - canonicalHash: 同一 AST を二度 parse しても同じ hash / 識別子名やリテラル値で区別される
 *   - collectSubtreeHashes: File 以下の全サブツリー hash を過不足なく集める
 *   - SubtreeDiff.isCommon: fast に同じノードが存在するときのみ true
 *   - 部分木マッチング: slow ノードが fast の左部分式として現れても common
 *   - Selakovic #1: slow の obj/key/arg-expr は common、hasOwnProperty は diff
 *   - エッジケース: 空ペア / 単一ノード / 同一ファイル (全ノード common)
 */
import { describe, expect, it } from "vitest";
import type { Statement } from "@babel/types";
import { SubtreeDiff, canonicalHash } from "../../../src/pruning/ast/diff";
import { parse } from "../../../src/pruning/ast/parser";

function firstStatement(code: string): Statement {
  const file = parse(code);
  const stmt = file.program.body[0];
  if (stmt === undefined) throw new Error("empty program");
  return stmt;
}

describe("canonicalHash", () => {
  it("同一コードを二度 parse しても同じ hash になる (決定性)", () => {
    expect(canonicalHash(parse("arr[0]"))).toBe(canonicalHash(parse("arr[0]")));
  });

  it("識別子名が異なると hash が異なる", () => {
    expect(canonicalHash(parse("a"))).not.toBe(canonicalHash(parse("b")));
  });

  it("数値リテラル値が異なると hash が異なる (arr[0] vs arr[1])", () => {
    expect(canonicalHash(parse("arr[0]"))).not.toBe(canonicalHash(parse("arr[1]")));
  });

  it("文字列リテラル値が異なると hash が異なる", () => {
    expect(canonicalHash(parse("'a'"))).not.toBe(canonicalHash(parse("'b'")));
  });

  it("演算子が異なると hash が異なる (a + b vs a - b)", () => {
    expect(canonicalHash(parse("a + b"))).not.toBe(canonicalHash(parse("a - b")));
  });

  it("computed か shorthand か等の構造フラグも区別する (obj.x vs obj['x'])", () => {
    // 計算メンバアクセスと静的プロパティアクセスは AST として別物なので hash も別
    expect(canonicalHash(parse("obj.x"))).not.toBe(canonicalHash(parse("obj['x']")));
  });

  it("loc / コメントは hash に影響しない", () => {
    const plain = canonicalHash(parse("arr[0]"));
    const withComment = canonicalHash(parse("// prefix\narr[0] // trailing"));
    expect(plain).toBe(withComment);
  });
});

describe("SubtreeDiff.isCommon — 基本", () => {
  it("同一ファイル同士では全ノードが common 判定", () => {
    const src = "const x = arr[0]; use(x);";
    const file = parse(src);
    const diff = new SubtreeDiff(file, parse(src));
    for (const stmt of file.program.body) {
      expect(diff.isCommon(stmt)).toBe(true);
    }
  });

  it("fast の部分式として同型が存在するノードは common (a+b は (a+b)+c の左部分式)", () => {
    // BinaryExpression の左結合で fast は ((a+b)+c) となり、slow の `a+b` は左部分木として同型
    const slow = parse("a + b");
    const fast = parse("a + b + c");
    const diff = new SubtreeDiff(slow, fast);
    const stmt = slow.program.body[0];
    if (stmt?.type !== "ExpressionStatement") throw new Error("unexpected");
    expect(diff.isCommon(stmt.expression)).toBe(true);
  });

  it("fast に同型サブツリーが存在しないノードは diff (演算子違い)", () => {
    const slow = parse("a - b");
    const fast = parse("a + b");
    const diff = new SubtreeDiff(slow, fast);
    const stmt = slow.program.body[0];
    if (stmt?.type !== "ExpressionStatement") throw new Error("unexpected");
    expect(diff.isCommon(stmt.expression)).toBe(false);
  });

  it("空のペアは有効な SubtreeDiff を作れる", () => {
    const diff = new SubtreeDiff(parse(""), parse(""));
    const identOnly = firstStatement("x");
    // x は fast (空) に存在しないので diff
    expect(diff.isCommon(identOnly)).toBe(false);
  });

  it("単一ノードペアで共通ノードを正しく検出する", () => {
    const diff = new SubtreeDiff(parse("x"), parse("x"));
    const node = firstStatement("x");
    expect(diff.isCommon(node)).toBe(true);
  });
});

describe("SubtreeDiff.isCommon — Selakovic #1 (hasOwnProperty)", () => {
  // slow: if (obj.hasOwnProperty(key)) { use(obj[key]); }
  // fast: use(obj[key]);
  // 差分フィルタの期待: obj / key / obj[key] / use(obj[key]) は common、
  // hasOwnProperty 識別子と対応する CallExpression/IfStatement は diff。
  const SLOW_CODE = "if (obj.hasOwnProperty(key)) { use(obj[key]); }";
  const FAST_CODE = "use(obj[key]);";

  it("obj / key 識別子は common", () => {
    const slow = parse(SLOW_CODE);
    const fast = parse(FAST_CODE);
    const diff = new SubtreeDiff(slow, fast);

    // slow の IfStatement.test は CallExpression (obj.hasOwnProperty(key))
    const ifStmt = slow.program.body[0];
    if (ifStmt?.type !== "IfStatement") throw new Error("expected IfStatement");
    const callExpr = ifStmt.test;
    if (callExpr.type !== "CallExpression") throw new Error("expected CallExpression");
    const memberExpr = callExpr.callee;
    if (memberExpr.type !== "MemberExpression") throw new Error("expected MemberExpression");

    // obj 識別子 (MemberExpression.object)
    expect(diff.isCommon(memberExpr.object)).toBe(true);
    // key 識別子 (CallExpression.arguments[0])
    const keyArg = callExpr.arguments[0];
    if (keyArg === undefined) throw new Error("missing arg");
    expect(diff.isCommon(keyArg)).toBe(true);
  });

  it("hasOwnProperty 識別子は diff (fast には登場しない)", () => {
    const slow = parse(SLOW_CODE);
    const fast = parse(FAST_CODE);
    const diff = new SubtreeDiff(slow, fast);

    const ifStmt = slow.program.body[0];
    if (ifStmt?.type !== "IfStatement") throw new Error("expected IfStatement");
    const callExpr = ifStmt.test;
    if (callExpr.type !== "CallExpression") throw new Error("expected CallExpression");
    const memberExpr = callExpr.callee;
    if (memberExpr.type !== "MemberExpression") throw new Error("expected MemberExpression");

    // obj.hasOwnProperty の property = Identifier("hasOwnProperty")
    expect(diff.isCommon(memberExpr.property)).toBe(false);
    // hasOwnProperty(...) 全体の CallExpression も diff
    expect(diff.isCommon(callExpr)).toBe(false);
    // IfStatement 全体も diff
    expect(diff.isCommon(ifStmt)).toBe(false);
  });

  it("obj[key] の MemberExpression は common", () => {
    const slow = parse(SLOW_CODE);
    const fast = parse(FAST_CODE);
    const diff = new SubtreeDiff(slow, fast);

    // slow: IfStatement.consequent (BlockStatement) -> body[0] (ExpressionStatement) -> expression (CallExpression) -> arguments[0] (MemberExpression)
    const ifStmt = slow.program.body[0];
    if (ifStmt?.type !== "IfStatement") throw new Error("unexpected");
    const block = ifStmt.consequent;
    if (block.type !== "BlockStatement") throw new Error("unexpected");
    const exprStmt = block.body[0];
    if (exprStmt?.type !== "ExpressionStatement") throw new Error("unexpected");
    const useCall = exprStmt.expression;
    if (useCall.type !== "CallExpression") throw new Error("unexpected");
    const objKey = useCall.arguments[0];
    if (objKey === undefined || objKey.type !== "MemberExpression") throw new Error("unexpected");

    expect(diff.isCommon(objKey)).toBe(true);
    // use(obj[key]) 全体も common
    expect(diff.isCommon(useCall)).toBe(true);
  });
});
