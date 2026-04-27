import type { File, Node } from "@babel/types";

import { tryGenerateNode } from "./parser";

/**
 * AST 上のノード集計・元コード抽出など、副作用なしの read-only 検査ユーティリティ。
 */

/**
 * File に含まれるノード総数を数える。`type` プロパティを持つオブジェクトを
 * ノードとみなす単純走査で、循環参照は想定しない (Babel AST は非循環)。
 */
export function countNodes(file: File): number {
  let count = 0;
  function walk(node: unknown): void {
    if (node === null || node === undefined) return;
    if (Array.isArray(node)) {
      for (const n of node as unknown[]) walk(n);
      return;
    }
    if (typeof node !== "object") return;
    const obj = node as { type?: unknown };
    if (typeof obj.type !== "string") return;
    count += 1;
    for (const [, v] of Object.entries(node as Record<string, unknown>)) {
      if (v !== null && typeof v === "object") walk(v);
    }
  }
  walk(file);
  return count;
}

/**
 * 候補ノードの元スニペットを再構成する。start/end が取れれば元コードから切り出し、
 * 取れなければ generate で近似。第 2 段階で参照するのは「何を置換したか」の情報。
 */
export function snippetOfNode(node: Node, sourceCode: string): string {
  const start = node.start;
  const end = node.end;
  if (typeof start === "number" && typeof end === "number" && end >= start) {
    return sourceCode.slice(start, end);
  }
  return tryGenerateNode(node);
}
