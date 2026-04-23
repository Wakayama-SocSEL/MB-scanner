import { VISITOR_KEYS } from "@babel/types";
import type { File, Node } from "@babel/types";

/**
 * slow のノードごとに「fast のどこかに同じノードがあるか」を判定する。
 *
 * 「同じ」はハッシュによる厳密一致で、タイプ・子・識別子名・リテラル値・演算子が
 * すべて揃って初めて同じ扱い。例えば `arr[0]` と `arr[1]` は別物になる。
 *
 * 採用判断 (top-down subtree hash 自作 / bottom-up は非採用):
 *   - ai-guide/adr/0002-babel-topdown-subtree-hash.md
 *   - ai-guide/adr/0003-bottom-up-mapping-deferred.md
 */
export class SubtreeDiff {
  private readonly fastHashes: Set<string>;

  constructor(_slow: File, fast: File) {
    this.fastHashes = collectSubtreeHashes(fast);
  }

  /** node と同じノードが fast のどこかにあるか。 */
  isCommon(node: Node): boolean {
    return this.fastHashes.has(canonicalHash(node));
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

function isNode(value: unknown): value is Node {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof value.type === "string"
  );
}

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
export function canonicalHash(node: Node): string {
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
export function collectSubtreeHashes(file: File): Set<string> {
  const set = new Set<string>();

  function walk(node: Node): void {
    set.add(canonicalHash(node));
    const visitorKeys = VISITOR_KEYS[node.type] ?? [];
    const record = node as unknown as Record<string, unknown>;
    for (const key of visitorKeys) {
      const child = record[key];
      if (child === null || child === undefined) continue;
      if (Array.isArray(child)) {
        for (const c of child) {
          if (isNode(c)) walk(c);
        }
      } else if (isNode(child)) {
        walk(child);
      }
    }
  }

  walk(file);
  return set;
}
