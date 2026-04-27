import generateModule from "@babel/generator";
import {
  emptyStatement,
  identifier,
  stringLiteral,
  VISITOR_KEYS,
} from "@babel/types";
import type { File, Node } from "@babel/types";

import { parse } from "./parser";

/**
 * 候補 1 箇所だけを置換した新しい File AST を生成する。
 *
 *   - **非破壊**: 元 AST は一切変更せず、deep copy した上で 1 箇所だけ差し替える
 *   - **round-trip 検証**: generate → parse で構文的に復元可能か確認。復元できない
 *     置換 (親子型不整合など) は `null` を返して engine 側がスキップする
 *
 * 置換モード:
 *   - `deleteStatement`: Statement を EmptyStatement (`;`) に置換
 *   - `wildcardIdentifier`: Identifier を `$VAR` に置換
 *   - `wildcardExpression`: Expression を StringLiteral (`"$EXPR"`) に置換
 *     (親が Expression を期待する位置で最も無害な Expression リテラルを使う)
 */

export type ReplacementMode =
  | "deleteStatement"
  | "wildcardIdentifier"
  | "wildcardExpression";

export interface ReplaceInput {
  /** 元 File AST。関数は clone するため、入力は変更されない。 */
  readonly file: File;
  /** 置換対象の親ノード (enumerateCandidates の CandidatePath.parent と同一の位置)。 */
  readonly parent: Node;
  readonly parentKey: string;
  /** 親の該当 key が配列のときのインデックス。スカラ子なら undefined。 */
  readonly listIndex?: number | undefined;
  readonly mode: ReplacementMode;
  /** wildcard の表示名 (ID)。`$ITER`, `$BODY` など呼び出し側で採番。 */
  readonly placeholderId: string;
}

export interface ReplaceResult {
  readonly file: File;
  /** `file` を `@babel/generator` で文字列化した結果。 */
  readonly code: string;
}

/**
 * 1 箇所書き換えを行う。round-trip で parse 可能な場合のみ結果を返す。
 *
 * 親ノードは clone された AST 上で位置参照で特定する必要があるので、`parent` と
 * `parentKey` / `listIndex` から clone 後の同じ位置を辿り直す。辿り直しは「元 File
 * 上で parent と同じ visitor 経路を下る」方針で、parent が直接参照で一致するまで
 * 走査する (AST 木は通常 100〜1000 ノード程度なので線形探索で十分)。
 */
export function replaceNode(input: ReplaceInput): ReplaceResult | null {
  const clone = cloneAst(input.file);
  const clonedParent = findCorrespondingNode(input.file, clone, input.parent);
  if (clonedParent === null) return null;

  const replacement = buildReplacement(input.mode, input.placeholderId);
  if (replacement === null) return null;

  if (!applyReplacement(clonedParent, input.parentKey, input.listIndex, replacement)) {
    return null;
  }

  // Babel の generate は ESM/CJS の wrapper が環境によって異なる (default export)
  const generator = (generateModule as unknown as { default?: typeof generateModule })
    .default ?? generateModule;
  let code: string;
  try {
    code = generator(clone).code;
  } catch {
    return null;
  }

  // round-trip: 置換結果を parse し直してみる。失敗したら候補スキップ。
  let reparsed: File;
  try {
    reparsed = parse(code);
  } catch {
    return null;
  }

  return { file: reparsed, code };
}

function buildReplacement(mode: ReplacementMode, placeholderId: string): Node | null {
  switch (mode) {
    case "deleteStatement":
      return emptyStatement();
    case "wildcardIdentifier":
      return identifier(sanitizeIdentifier(placeholderId));
    case "wildcardExpression":
      return stringLiteral(placeholderId);
    default: {
      const exhaustive: never = mode;
      void exhaustive;
      return null;
    }
  }
}

/**
 * Babel identifier 名の制約 (英数字 + `_` + `$` のみ) を満たすよう placeholderId を
 * 正規化する。先頭は数字不可なので数字なら `_` を先頭に足す。
 */
function sanitizeIdentifier(placeholderId: string): string {
  const cleaned = placeholderId.replace(/[^A-Za-z0-9_$]/g, "_");
  if (cleaned.length === 0) return "$VAR";
  if (/^[0-9]/.test(cleaned)) return `_${cleaned}`;
  return cleaned;
}

function applyReplacement(
  parent: Node,
  parentKey: string,
  listIndex: number | undefined,
  replacement: Node,
): boolean {
  const record = parent as unknown as Record<string, unknown>;
  if (listIndex === undefined) {
    record[parentKey] = replacement;
    return true;
  }
  const arr = record[parentKey];
  if (!Array.isArray(arr)) return false;
  if (listIndex < 0 || listIndex >= arr.length) return false;
  (arr as Node[])[listIndex] = replacement;
  return true;
}

/**
 * `source` AST 上の `target` ノードと同じパスにある `cloned` AST 上のノードを返す。
 *
 * clone 後は参照が変わっているので、親を再特定するために元 AST を走査して target
 * と参照が一致する位置を見つけ、同時に clone 側を同じ経路で辿る。見つからなければ
 * null (通常は呼び出し側のバグ)。
 */
function findCorrespondingNode(source: File, cloned: File, target: Node): Node | null {
  let found: Node | null = null;

  function walk(src: Node, clo: Node): void {
    if (found !== null) return;
    if (src === target) {
      found = clo;
      return;
    }
    const visitorKeys = VISITOR_KEYS[src.type] ?? [];
    const srcRec = src as unknown as Record<string, unknown>;
    const cloRec = clo as unknown as Record<string, unknown>;
    for (const key of visitorKeys) {
      const srcChild = srcRec[key];
      const cloChild = cloRec[key];
      if (srcChild === null || srcChild === undefined) continue;
      if (Array.isArray(srcChild) && Array.isArray(cloChild)) {
        for (let i = 0; i < srcChild.length; i++) {
          const s = srcChild[i] as unknown;
          const c = cloChild[i] as unknown;
          if (isNode(s) && isNode(c)) walk(s, c);
          if (found !== null) return;
        }
      } else if (isNode(srcChild) && isNode(cloChild)) {
        walk(srcChild, cloChild);
      }
    }
  }

  walk(source, cloned);
  return found;
}

/**
 * Babel AST を VISITOR_KEYS ベースで deep copy する。
 *
 * `structuredClone` は Babel の Node に付いている自己参照や関数プロパティで落ちる
 * ため自前実装する。copy 対象は「VISITOR_KEYS で辿れる子」と「リーフの value 系
 * プロパティ」のみ。loc/comments などのメタは値コピー (再 parse で再計算される)。
 */
function cloneAst<T extends Node>(node: T): T {
  const visitorKeys = VISITOR_KEYS[node.type] ?? [];
  const visitorKeySet = new Set<string>(visitorKeys);
  const record = node as unknown as Record<string, unknown>;
  const copy: Record<string, unknown> = {};

  for (const key of Object.keys(record)) {
    const value = record[key];
    if (visitorKeySet.has(key)) {
      copy[key] = cloneChild(value);
    } else {
      copy[key] = value;
    }
  }
  return copy as T;
}

function cloneChild(value: unknown): unknown {
  if (value === null || value === undefined) return value;
  if (Array.isArray(value)) {
    const arr: unknown[] = value as unknown[];
    return arr.map((v) => (isNode(v) ? cloneAst(v) : v));
  }
  if (isNode(value)) return cloneAst(value);
  return value;
}

function isNode(value: unknown): value is Node {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as { type: unknown }).type === "string"
  );
}
