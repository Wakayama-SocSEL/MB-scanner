/**
 * 対象: src/pruning/ast/inspect.ts (read-only AST 検査ユーティリティ)
 *
 * 観点:
 *   - countNodes: File に含まれる全ノードを type プロパティで判定し再帰カウント
 *   - snippetOfNode: start/end が取れれば元コード切り出し、無ければ generate fallback
 */
import * as t from "@babel/types";
import { describe, expect, it } from "vitest";

import { countNodes, snippetOfNode } from "../../../src/pruning/ast/inspect";
import { parse } from "../../../src/pruning/ast/parser";

describe("countNodes", () => {
  it("空 File は最低限の構造ノード (File / Program) を数える", () => {
    const file = parse("");
    // File + Program で 2
    expect(countNodes(file)).toBe(2);
  });

  it("単純な statement のノード数を数える", () => {
    const file = parse("const x = 1;");
    // File / Program / VariableDeclaration / VariableDeclarator / Identifier / NumericLiteral
    expect(countNodes(file)).toBe(6);
  });

  it("ノード数は構造の複雑さに応じて増える", () => {
    const simple = parse("x;");
    const complex = parse("if (a) { f(b, c); } else { g(d); }");
    expect(countNodes(complex)).toBeGreaterThan(countNodes(simple));
  });

  it("入れ子は再帰的に数える", () => {
    const flat = parse("a + b;");
    const nested = parse("a + b + c + d;");
    // BinaryExpression が 1 つ増えるごとにノードが追加される
    expect(countNodes(nested)).toBeGreaterThan(countNodes(flat));
  });
});

describe("snippetOfNode", () => {
  it("start/end が取れる場合は元ソースから正確に切り出す", () => {
    const code = "const x = arr[0]; use(x);";
    const file = parse(code);
    const decl = file.program.body[0];
    expect(decl?.type).toBe("VariableDeclaration");
    expect(snippetOfNode(decl as t.Node, code)).toBe("const x = arr[0];");
  });

  it("内側ノードでも正確に切り出す", () => {
    const code = "const x = arr[0]; use(x);";
    const file = parse(code);
    const decl = file.program.body[0] as t.VariableDeclaration;
    const init = decl.declarations[0]?.init;
    expect(init?.type).toBe("MemberExpression");
    expect(snippetOfNode(init as t.Node, code)).toBe("arr[0]");
  });

  it("start/end が無いノードは generate で近似する", () => {
    // 手動構築したノードは start/end を持たない
    const node = t.numericLiteral(42);
    const snippet = snippetOfNode(node, "");
    expect(snippet).toBe("42");
  });

  it("generate も失敗するような不完全ノードは空文字を返す (defensive)", () => {
    // type だけ持つ broken ノード
    const broken = { type: "NotARealType" } as unknown as t.Node;
    expect(snippetOfNode(broken, "")).toBe("");
  });
});
