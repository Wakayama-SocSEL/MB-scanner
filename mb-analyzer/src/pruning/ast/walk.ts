import { VISITOR_KEYS } from "@babel/types";
import type { Node } from "@babel/types";

/**
 * Babel AST を `VISITOR_KEYS` ベースで深さ優先に走査する共通機構。
 *
 * 判断: ai-guide/adr/0001-pruning-ast-traversal.md
 */

export interface VisitContext {
  readonly node: Node;
  readonly parent: Node | null;
  readonly parentKey: string | null;
  readonly listIndex: number | undefined;
}

/**
 * `root` を起点に AST を DFS 走査し、各ノードで `visit` を呼ぶ。
 *
 * `parent` / `parentKey` / `listIndex` は root では `null` / `null` / `undefined` で、
 * 子に降りる際に親情報が埋まる。配列子 (`body[i]` 等) では `listIndex` が付き、単一子では
 * `undefined`。子が `null` / `undefined` の slot や Node でないリーフ (リテラル値等) は
 * skip する。
 */
export function walkNodes(root: Node, visit: (ctx: VisitContext) => void): void {
  function go(
    node: Node,
    parent: Node | null,
    parentKey: string | null,
    listIndex: number | undefined,
  ): void {
    visit({ node, parent, parentKey, listIndex });
    const visitorKeys = VISITOR_KEYS[node.type] ?? [];
    const record = node as unknown as Record<string, unknown>;
    for (const key of visitorKeys) {
      const child = record[key];
      if (child === null || child === undefined) continue;
      if (Array.isArray(child)) {
        for (let i = 0; i < child.length; i++) {
          const c = child[i] as unknown;
          if (isNode(c)) go(c, node, key, i);
        }
      } else if (isNode(child)) {
        go(child, node, key, undefined);
      }
    }
  }
  go(root, null, null, undefined);
}

/**
 * Babel `Node` の型ガード。`comments` / `tokens` のように `type` を持つが Node では
 * ないメタ情報は通過しない。
 */
export function isNode(value: unknown): value is Node {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
}

// 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;

  const stubNode = (type: string, extra: Record<string, unknown> = {}): Node =>
    ({ type, ...extra }) as unknown as Node;

  describe("walkNodes (in-source)", () => {
    it("root は parent=null / parentKey=null / listIndex=undefined で visit される", () => {
      const visited: VisitContext[] = [];
      walkNodes(stubNode("Identifier"), (ctx) => visited.push(ctx));
      expect(visited).toHaveLength(1);
      expect(visited[0]?.parent).toBeNull();
      expect(visited[0]?.parentKey).toBeNull();
      expect(visited[0]?.listIndex).toBeUndefined();
    });

    it("VISITOR_KEYS に登録の無い型でも crash せず単発で終わる", () => {
      // 将来 Babel に追加される未知型 / 自作型を想定
      const visited: VisitContext[] = [];
      expect(() =>
        walkNodes(stubNode("__UnknownNonStandardType__"), (ctx) => visited.push(ctx)),
      ).not.toThrow();
      expect(visited).toHaveLength(1);
    });
  });

  describe("isNode (in-source)", () => {
    it("`{ type: string }` の object は Node 扱い", () => {
      expect(isNode({ type: "Identifier" })).toBe(true);
    });

    it("type を持たない object / null / プリミティブは false", () => {
      expect(isNode({ name: "x" })).toBe(false);
      expect(isNode(null)).toBe(false);
      expect(isNode("Identifier")).toBe(false);
      expect(isNode(undefined)).toBe(false);
    });

    it("type が string でない場合は false", () => {
      expect(isNode({ type: 42 })).toBe(false);
    });
  });
}
