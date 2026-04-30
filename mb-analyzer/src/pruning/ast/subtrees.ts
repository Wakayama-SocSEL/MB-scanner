import { VISITOR_KEYS } from "@babel/types";
import type { File, Node } from "@babel/types";

import { walkNodes } from "./walk";

/**
 * fast 側のサブツリー集合への所属判定器。`has(node)` で node と同型のサブツリーが
 * fast のどこかに存在するかを返す。
 *
 * 「同型」はハッシュによる厳密一致で、タイプ・子・識別子名・リテラル値・演算子が
 * すべて揃って初めて同型と扱う。例えば `arr[0]` と `arr[1]` は別物。実装は内部
 * `canonicalHash` で文字列化した `Set<string>` だが、外部からはサブツリー集合
 * として扱う API のみを公開する。
 *
 * 採用判断 (top-down subtree hash 自作 / bottom-up は非採用):
 *   - ai-guide/adr/0002-babel-topdown-subtree-hash.md
 *   - ai-guide/adr/0003-bottom-up-mapping-deferred.md
 */
export class FastSubtreeSet {
  private readonly hashes: Set<string>;

  constructor(fast: File) {
    this.hashes = collectSubtreeHashes(fast);
  }

  /** node と同型のサブツリーが fast のどこかに含まれるか。 */
  has(node: Node): boolean {
    return this.hashes.has(canonicalHash(node));
  }
}

// Babel AST ノードには loc / start / end / comments / extra などソース位置・表示系の
// プロパティが含まれる。同じコードを再 parse しても微妙にぶれる値が多いので、ハッシュ
// からはまとめて除外する。
const METADATA_KEYS: ReadonlySet<string> = new Set([
  "type",
  "loc",
  "start",
  "end",
  "range",
  "leadingComments",
  "trailingComments",
  "innerComments",
  "extra",
  "trailingComma",
  "comments",
  "errors",
]);

// VISITOR_KEYS で辿れる子は Node / null / それらの配列のいずれか。
type VisitorChild = Node | null | undefined | Array<Node | null | undefined>;

function hashChild(child: VisitorChild): string {
  if (child === null || child === undefined) return "_";
  if (Array.isArray(child)) {
    return `[${child.map(hashChild).join(",")}]`;
  }
  return canonicalHash(child);
}

/**
 * ノードの正規化ハッシュ。
 *
 * タイプ・子ノード・識別子名・リテラル値・演算子・`computed` などの構造フラグが
 * 全部一致すれば等しいハッシュを持つ。ソース位置・コメント・`extra` (原表記情報)
 * は計算に含めない — METADATA_KEYS 参照。
 */
function canonicalHash(node: Node): string {
  const visitorKeys = VISITOR_KEYS[node.type] ?? [];
  const visitorKeySet = new Set<string>(visitorKeys);

  const record = node as unknown as Record<string, unknown>;
  const valueEntries: string[] = [];
  for (const key of Object.keys(record).sort()) {
    if (METADATA_KEYS.has(key)) continue;
    if (visitorKeySet.has(key)) continue;
    const value = record[key];
    if (value === undefined) continue;
    valueEntries.push(`${key}=${JSON.stringify(value)}`);
  }

  const childEntries: string[] = [];
  for (const key of visitorKeys) {
    childEntries.push(`${key}=${hashChild(record[key] as VisitorChild)}`);
  }

  return `${node.type}{${valueEntries.join(",")}}(${childEntries.join(",")})`;
}

// 判断: ai-guide/adr/0001-pruning-ast-traversal.md
/**
 * File とその全サブツリーのハッシュを Set で返す。
 */
function collectSubtreeHashes(file: File): Set<string> {
  const set = new Set<string>();
  walkNodes(file, ({ node }) => set.add(canonicalHash(node)));
  return set;
}

// 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;
  // parser は本 if ブロック内でだけ必要なので遅延 import (production bundle には残らない)
  const { parse } = await import("./parser");

  const firstStatement = (code: string) => {
    const stmt = parse(code).program.body[0];
    if (stmt === undefined) throw new Error("empty program");
    return stmt;
  };

  describe("canonicalHash (in-source)", () => {
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
      expect(canonicalHash(parse("obj.x"))).not.toBe(canonicalHash(parse("obj['x']")));
    });

    it("loc / コメントは hash に影響しない", () => {
      const plain = canonicalHash(parse("arr[0]"));
      const withComment = canonicalHash(parse("// prefix\narr[0] // trailing"));
      expect(plain).toBe(withComment);
    });
  });

  describe("collectSubtreeHashes (in-source)", () => {
    it("空の File は 2 要素 (File と Program) だけを持つ", () => {
      const hashes = collectSubtreeHashes(parse(""));
      expect(hashes.size).toBe(2);
    });

    it("サブツリーも漏れなく含まれる: arr[0] は arr 識別子・0 リテラル・MemberExpression を持つ", () => {
      const hashes = collectSubtreeHashes(parse("arr[0]"));

      const memberStmt = parse("arr[0]").program.body[0];
      if (memberStmt?.type !== "ExpressionStatement") throw new Error("unexpected");
      const memberExpr = memberStmt.expression;
      if (memberExpr.type !== "MemberExpression") throw new Error("unexpected");

      expect(hashes.has(canonicalHash(memberExpr))).toBe(true);
      expect(hashes.has(canonicalHash(memberExpr.object))).toBe(true); // arr (Identifier)
      expect(hashes.has(canonicalHash(memberExpr.property))).toBe(true); // 0 (NumericLiteral)
    });
  });

  describe("FastSubtreeSet.has (in-source) — 基本", () => {
    it("同一ファイル同士では全ノードが common 判定", () => {
      const src = "const x = arr[0]; use(x);";
      const file = parse(src);
      const diff = new FastSubtreeSet(parse(src));
      for (const stmt of file.program.body) {
        expect(diff.has(stmt)).toBe(true);
      }
    });

    it("fast の部分式として同型が存在するノードは common (a+b は (a+b)+c の左部分式)", () => {
      const slow = parse("a + b");
      const fast = parse("a + b + c");
      const diff = new FastSubtreeSet(fast);
      const stmt = slow.program.body[0];
      if (stmt?.type !== "ExpressionStatement") throw new Error("unexpected");
      expect(diff.has(stmt.expression)).toBe(true);
    });

    it("fast に同型サブツリーが存在しないノードは diff (演算子違い)", () => {
      const slow = parse("a - b");
      const fast = parse("a + b");
      const diff = new FastSubtreeSet(fast);
      const stmt = slow.program.body[0];
      if (stmt?.type !== "ExpressionStatement") throw new Error("unexpected");
      expect(diff.has(stmt.expression)).toBe(false);
    });

    it("空のペアは有効な FastSubtreeSet を作れる", () => {
      const diff = new FastSubtreeSet(parse(""));
      const identOnly = firstStatement("x");
      expect(diff.has(identOnly)).toBe(false);
    });

    it("単一ノードペアで共通ノードを正しく検出する", () => {
      const diff = new FastSubtreeSet(parse("x"));
      const node = firstStatement("x");
      expect(diff.has(node)).toBe(true);
    });
  });

  describe("FastSubtreeSet.has (in-source) — Selakovic #1 (hasOwnProperty)", () => {
    // slow: if (obj.hasOwnProperty(key)) { use(obj[key]); }
    // fast: use(obj[key]);
    // 差分フィルタの期待: obj / key / obj[key] / use(obj[key]) は common、
    // hasOwnProperty 識別子と対応する CallExpression/IfStatement は diff。
    const SLOW_CODE = "if (obj.hasOwnProperty(key)) { use(obj[key]); }";
    const FAST_CODE = "use(obj[key]);";

    it("obj / key 識別子は common", () => {
      const slow = parse(SLOW_CODE);
      const fast = parse(FAST_CODE);
      const diff = new FastSubtreeSet(fast);

      const ifStmt = slow.program.body[0];
      if (ifStmt?.type !== "IfStatement") throw new Error("expected IfStatement");
      const callExpr = ifStmt.test;
      if (callExpr.type !== "CallExpression") throw new Error("expected CallExpression");
      const memberExpr = callExpr.callee;
      if (memberExpr.type !== "MemberExpression") throw new Error("expected MemberExpression");

      expect(diff.has(memberExpr.object)).toBe(true); // obj
      const keyArg = callExpr.arguments[0];
      if (keyArg === undefined) throw new Error("missing arg");
      expect(diff.has(keyArg)).toBe(true); // key
    });

    it("hasOwnProperty 識別子は diff (fast には登場しない)", () => {
      const slow = parse(SLOW_CODE);
      const fast = parse(FAST_CODE);
      const diff = new FastSubtreeSet(fast);

      const ifStmt = slow.program.body[0];
      if (ifStmt?.type !== "IfStatement") throw new Error("expected IfStatement");
      const callExpr = ifStmt.test;
      if (callExpr.type !== "CallExpression") throw new Error("expected CallExpression");
      const memberExpr = callExpr.callee;
      if (memberExpr.type !== "MemberExpression") throw new Error("expected MemberExpression");

      expect(diff.has(memberExpr.property)).toBe(false); // hasOwnProperty
      expect(diff.has(callExpr)).toBe(false);
      expect(diff.has(ifStmt)).toBe(false);
    });

    it("obj[key] の MemberExpression は common", () => {
      const slow = parse(SLOW_CODE);
      const fast = parse(FAST_CODE);
      const diff = new FastSubtreeSet(fast);

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

      expect(diff.has(objKey)).toBe(true);
      expect(diff.has(useCall)).toBe(true);
    });
  });
}
