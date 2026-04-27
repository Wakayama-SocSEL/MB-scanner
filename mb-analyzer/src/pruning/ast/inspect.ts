import { VISITOR_KEYS } from "@babel/types";
import type { File, Node } from "@babel/types";

import { tryGenerateNode } from "./parser";

/**
 * AST 上のノード集計・元コード抽出など、副作用なしの read-only 検査ユーティリティ。
 */

/**
 * File に含まれる AST ノード総数を `VISITOR_KEYS` ベースで数える。
 * `comments` / `tokens` のように `type` を持つが Node ではないメタ情報は対象外。
 */
export function countNodes(file: File): number {
  let count = 0;
  function walk(node: Node): void {
    count += 1;
    const visitorKeys = VISITOR_KEYS[node.type] ?? [];
    const record = node as unknown as Record<string, unknown>;
    for (const key of visitorKeys) {
      const child = record[key];
      if (child === null || child === undefined) continue;
      if (Array.isArray(child)) {
        for (const c of child as unknown[]) {
          if (isNode(c)) walk(c);
        }
      } else if (isNode(child)) {
        walk(child);
      }
    }
  }
  walk(file);
  return count;
}

function isNode(value: unknown): value is Node {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
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
