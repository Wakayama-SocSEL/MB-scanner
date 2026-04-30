/**
 * 対象: src/pruning/candidates.ts (`enumerateCandidates` の責務統合)
 *
 * 観点 (各責務が `enumerateCandidates` 内で正しく連携することを確認):
 *   - whitelist 連携: `NODE_CATEGORY` に含まれる型のみ候補化
 *   - blacklist 連携: `getGrammarBlacklist()` の判定が enumerate 時に効く
 *   - SubtreeDiff 連携: 差分ノードが除外される (diff 渡し有無で挙動が変わる)
 *   - CandidatePath 構造: parent / parentKey / listIndex の組み立て
 *   - サイズ降順ソート
 *
 * 位置別 ExcludeRule の正確性は `rules/blacklist.test.ts` で個別検証する
 * (本ファイルでは「整合した結果が得られる」レベルで止める)。
 */
import { describe, expect, it } from "vitest";
import type { Node } from "@babel/types";
import { enumerateCandidates } from "../../src/pruning/candidates";
import { SubtreeDiff } from "../../src/pruning/ast/diff";
import { parse } from "../../src/pruning/ast/parser";

function types(nodes: Iterable<{ node: Node }>): string[] {
  return [...nodes].map((c) => c.node.type);
}

describe("enumerateCandidates — whitelist 連携", () => {
  it("NODE_CATEGORY の 3 カテゴリすべてから候補が拾われる", () => {
    const slow = parse("if (c) { use(arr[0]); }");
    const ts = types(enumerateCandidates(slow));
    expect(ts).toContain("IfStatement");      // statement
    expect(ts).toContain("BlockStatement");   // statement
    expect(ts).toContain("CallExpression");   // expression
    expect(ts).toContain("MemberExpression"); // expression
    expect(ts).toContain("NumericLiteral");   // expression
    expect(ts).toContain("Identifier");       // identifier
  });

  it("NODE_CATEGORY 外の型 (VariableDeclarator / Program / File) は候補に入らない", () => {
    const slow = parse("const x = 1;");
    const ts = types(enumerateCandidates(slow));
    expect(ts).not.toContain("VariableDeclarator");
    expect(ts).not.toContain("Program");
    expect(ts).not.toContain("File");
  });
});

describe("enumerateCandidates — blacklist 連携", () => {
  it("blacklist で除外される位置は候補から消える (代表例: VariableDeclarator.id の Identifier)", () => {
    const slow = parse("const x = arr[0];");
    const candidates = enumerateCandidates(slow);
    const onIdSlot = candidates.filter(
      (c) => c.parent.type === "VariableDeclarator" && c.parentKey === "id",
    );
    expect(onIdSlot).toHaveLength(0);
  });

  it("blacklist 対象でない位置は同じ型でも通常通り候補化される (init 側)", () => {
    const slow = parse("const x = arr[0];");
    const candidates = enumerateCandidates(slow);
    const onInit = candidates.filter(
      (c) => c.parent.type === "VariableDeclarator" && c.parentKey === "init",
    );
    expect(onInit.length).toBeGreaterThan(0);
    expect(onInit[0]?.node.type).toBe("MemberExpression");
  });

  it("discriminator 条件付き blacklist が computed 値で切り替わる (MemberExpression.property)", () => {
    // computed=false: `obj.x` の `x` は blacklist (Identifier-only 位置)
    // computed=true:  `obj[expr]` の `expr` は blacklist 対象外
    const slow = parse("obj.x + obj[k];");
    const candidates = enumerateCandidates(slow);
    const onProperty = candidates.filter(
      (c) => c.parent.type === "MemberExpression" && c.parentKey === "property",
    );
    // computed=true の `k` (Identifier) のみ残る
    expect(onProperty).toHaveLength(1);
    const parent = onProperty[0]?.parent as { computed?: boolean } | undefined;
    expect(parent?.computed).toBe(true);
  });
});

describe("enumerateCandidates — SubtreeDiff 連携", () => {
  // slow にだけ存在する差分ノードが diff フィルタで除外されるかの統合確認。
  // CallExpression.arguments[1] は blacklist 対象外なので、diff の有無で候補入りが
  // 純粋に切り替わる。
  const SLOW_CODE = "use(key, flag);";
  const FAST_CODE = "use(key);";

  it("差分ノードは diff 渡し時に除外される", () => {
    const slow = parse(SLOW_CODE);
    const fast = parse(FAST_CODE);
    const diff = new SubtreeDiff(slow, fast);

    const candidates = enumerateCandidates(slow, diff);
    const flagIdent = candidates.find(
      (c) =>
        c.node.type === "Identifier" && (c.node as { name?: string }).name === "flag",
    );
    expect(flagIdent).toBeUndefined();
  });

  it("共通ノードは diff 渡し時にも候補に入る", () => {
    const slow = parse(SLOW_CODE);
    const fast = parse(FAST_CODE);
    const diff = new SubtreeDiff(slow, fast);

    const candidates = enumerateCandidates(slow, diff);
    const keyIdents = candidates.filter(
      (c) =>
        c.node.type === "Identifier" && (c.node as { name?: string }).name === "key",
    );
    expect(keyIdents.length).toBeGreaterThan(0);
  });

  it("diff を渡さなければ差分フィルタは無効化される", () => {
    const slow = parse(SLOW_CODE);
    const candidates = enumerateCandidates(slow);
    const flagIdent = candidates.find(
      (c) =>
        c.node.type === "Identifier" && (c.node as { name?: string }).name === "flag",
    );
    expect(flagIdent).toBeDefined();
  });
});

describe("enumerateCandidates — CandidatePath 構造", () => {
  it("配列子は listIndex 付き、スカラ子は listIndex なし", () => {
    const slow = parse("if (c) { a(); b(); }");
    const candidates = enumerateCandidates(slow);

    // BlockStatement.body[i] は配列子 → listIndex 必須
    const blockChildren = candidates.filter(
      (c) => c.parent.type === "BlockStatement" && c.parentKey === "body",
    );
    expect(blockChildren.length).toBeGreaterThan(0);
    expect(blockChildren.every((c) => typeof c.listIndex === "number")).toBe(true);

    // IfStatement.test はスカラ子 → listIndex なし
    const ifTest = candidates.find(
      (c) => c.parent.type === "IfStatement" && c.parentKey === "test",
    );
    expect(ifTest).toBeDefined();
    expect(ifTest?.listIndex).toBeUndefined();
  });
});

describe("enumerateCandidates — ソート", () => {
  it("サイズ降順 (start/end 幅) でソートされる", () => {
    const slow = parse("if (c) { const x = arr[0]; use(x); }");
    const candidates = enumerateCandidates(slow);
    // 最大ノードは IfStatement
    expect(candidates[0]?.node.type).toBe("IfStatement");
    const sizes = candidates.map((c) => (c.node.end ?? 0) - (c.node.start ?? 0));
    for (let i = 0; i < sizes.length - 1; i++) {
      const a = sizes[i];
      const b = sizes[i + 1];
      if (a === undefined || b === undefined) throw new Error("bounds");
      expect(a).toBeGreaterThanOrEqual(b);
    }
  });
});
