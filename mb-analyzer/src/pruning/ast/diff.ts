import { VISITOR_KEYS } from "@babel/types";
import type { File, Node } from "@babel/types";

/**
 * AST 差分フィルタ (GumTree top-down phase 相当)。
 *
 * slow 上のノード ``n`` について「fast のどこかに同型サブツリー ``n'`` が存在するか」を判定する。
 * 存在する場合そのノードは **共通 (common)**、しない場合は **差分 (diff)** と扱い、
 * pruning engine はこの判定を使って「必須ノード (= 差分)」を残し候補から除外する。
 *
 * 同型判定は正規化ハッシュによる厳密一致で行う。識別子名・リテラル値・構造を
 * 欠落なく保持するため、例えば ``arr[0]`` と ``arr[1]`` は異なるハッシュになる。
 *
 * 第 2 段階で必要になる bottom-up mapping (``mapTo``) は本 PR では未実装。
 */
export class SubtreeDiff {
  private readonly fastHashes: Set<string>;

  constructor(_slow: File, fast: File) {
    this.fastHashes = collectSubtreeHashes(fast);
  }

  isCommon(node: Node): boolean {
    return this.fastHashes.has(canonicalHash(node));
  }
}

// ---------------------------------------------------------------------------
// 純粋内部ヘルパ (module 内のみで使用、pruning/index.ts からは非 export)
// ---------------------------------------------------------------------------

// ノード型判定や子ノード検査では不要だがシリアライズでは保持してしまう
// メタデータ系キー。ハッシュには含めない。
// File ノードの ``comments`` / ``errors`` もソース位置情報を含むためここで弾く
// (``comments`` はそもそも差分判定に無関係、``errors`` は errorRecovery=false なら空)。
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
    typeof (value as { type: unknown }).type === "string"
  );
}

// VISITOR_KEYS で辿れる子は Babel の型定義上 Node | null | Array<Node | null> のみ。
// プリミティブは現れないのでここでは扱わない。
type VisitorChild = Node | null | undefined | Array<Node | null | undefined>;

function hashChild(child: VisitorChild): string {
  if (child === null || child === undefined) return "_";
  if (Array.isArray(child)) {
    return `[${child.map(hashChild).join(",")}]`;
  }
  return canonicalHash(child);
}

// ---------------------------------------------------------------------------
// テスト用に export している関数群
// (pruning/index.ts の public API には含めない。SubtreeDiff 経由の利用が正道で、
//  単体テストで hash 決定性・サブツリー走査を直接検証したいので限定公開する)
// ---------------------------------------------------------------------------

/**
 * 情報落ち最小の正規化ハッシュ。
 *
 * フォーマット: ``Type{valueFields}(childEntries)``
 * - valueFields: VISITOR_KEYS に含まれない own property を alphabetical 順に ``key=JSON`` 連結
 *   (識別子名 / リテラル値 / 演算子 / computed 等の構造的判定に必要な情報を保持)
 * - childEntries: VISITOR_KEYS で列挙される子ノード。null は ``_``、配列は ``[...]`` で包む
 *
 * 同一 AST を再度 parse したら同一ハッシュになる (``loc``/コメント/``extra`` は除外)。
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

/**
 * File 全体を再帰的に走査し、**全サブツリー**の canonical ハッシュを集める。
 *
 * ``@babel/traverse`` を使わず軽量な再帰で済ませているのは、traverse の NodePath 構築が
 * 数十〜数百倍遅いため。pruning は何度も呼ばれる hot path なので直書きしている。
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
