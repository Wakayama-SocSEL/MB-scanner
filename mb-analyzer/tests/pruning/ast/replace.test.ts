/**
 * 対象: src/pruning/ast/replace.ts (1 箇所書き換え)
 * 観点:
 *   - 非破壊: 元 AST は変更されない
 *   - 1 箇所書き換え: 他位置のノードは破壊されない
 *   - 3 つの置換モード (delete/identifier/expression) がそれぞれ意図通り動作
 *   - round-trip 検証: generate → parse で復元できる
 *   - 親子型不整合のケースは null で返る (Babel が弾くか parse が失敗する)
 */
import { describe, expect, it } from "vitest";
import type { File } from "@babel/types";

import { enumerateCandidates } from "../../../src/pruning/ast/candidates";
import { parse } from "../../../src/pruning/ast/parser";
import { replaceNode } from "../../../src/pruning/ast/replace";

function firstCandidate(file: File, predicate: (type: string) => boolean) {
  const candidates = enumerateCandidates(file);
  const found = candidates.find((c) => predicate(c.node.type));
  if (found === undefined) throw new Error("no candidate matched");
  return found;
}

describe("replaceNode — wildcardIdentifier", () => {
  it("Identifier を $VAR に置換できる", () => {
    const file = parse("use(key);");
    const c = firstCandidate(file, (t) => t === "Identifier");
    // use() の Identifier は 2 つあるので、どれかに置換
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardIdentifier",
      placeholderId: "$ITER",
    });
    expect(result).not.toBeNull();
    expect(result?.code).toContain("$ITER");
  });

  it("非識別子として無効な名前は _ にサニタイズされる", () => {
    const file = parse("use(key);");
    const c = firstCandidate(file, (t) => t === "Identifier");
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardIdentifier",
      placeholderId: "123bad",
    });
    // 先頭数字は `_123bad` に、そもそも parse 可能
    expect(result).not.toBeNull();
    expect(result?.code).toContain("_123bad");
  });
});

describe("replaceNode — wildcardExpression", () => {
  it("CallExpression 引数の式を $EXPR 文字列リテラルに置換できる", () => {
    const file = parse("use(key);");
    const c = firstCandidate(
      file,
      (t) => t === "Identifier" || t === "MemberExpression",
    );
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardExpression",
      placeholderId: "$P0",
    });
    expect(result).not.toBeNull();
    // 置換後は `use("$P0");` あるいは似た形になる
    expect(result?.code).toContain('"$P0"');
  });
});

describe("replaceNode — deleteStatement", () => {
  it("IfStatement を EmptyStatement に置換できる", () => {
    const file = parse("if (c) { a(); } b();");
    const c = firstCandidate(file, (t) => t === "IfStatement");
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "deleteStatement",
      placeholderId: "$P0",
    });
    expect(result).not.toBeNull();
    // 結果は `;\nb();` のような EmptyStatement + 残り
    expect(result?.code).toContain("b();");
    expect(result?.code).not.toContain("if ");
  });
});

describe("replaceNode — 非破壊性", () => {
  it("元 File の AST は変更されない (clone 経由)", () => {
    const file = parse("use(key);");
    const before = JSON.stringify(file, (key, value: unknown) =>
      key === "start" || key === "end" || key === "loc" ? undefined : value,
    );
    const c = firstCandidate(file, (t) => t === "Identifier");
    replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardIdentifier",
      placeholderId: "$VAR",
    });
    const after = JSON.stringify(file, (key, value: unknown) =>
      key === "start" || key === "end" || key === "loc" ? undefined : value,
    );
    expect(after).toBe(before);
  });

  it("1 箇所書き換えで他位置のノードは変わらない", () => {
    // `const x = arr[0]; use(x);` の `arr[0]` だけを置換し、`use(x)` は変わらない
    const file = parse("const x = arr[0]; use(x);");
    const c = firstCandidate(file, (t) => t === "MemberExpression");
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardExpression",
      placeholderId: "$P0",
    });
    expect(result).not.toBeNull();
    // `use(x)` はそのまま残る
    expect(result?.code).toContain("use(x)");
    // `arr[0]` 部分だけが `"$P0"` に置換される
    expect(result?.code).toContain('"$P0"');
    expect(result?.code).not.toContain("arr[0]");
  });
});

describe("replaceNode — round-trip", () => {
  it("置換結果が parser で復元できる場合のみ結果を返す", () => {
    const file = parse("use(key);");
    const c = firstCandidate(file, (t) => t === "Identifier");
    const result = replaceNode({
      file,
      parent: c.parent,
      parentKey: c.parentKey,
      ...(c.listIndex !== undefined ? { listIndex: c.listIndex } : {}),
      mode: "wildcardIdentifier",
      placeholderId: "$VAR",
    });
    expect(result).not.toBeNull();
    // 結果コードを再度 parse してエラーが起きない
    expect(() => parse(result!.code)).not.toThrow();
  });
});
