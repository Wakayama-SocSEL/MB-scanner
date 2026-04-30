import { emptyStatement, identifier, stringLiteral } from "@babel/types";
import type { Node } from "@babel/types";

import { PLACEHOLDER_KIND, type PlaceholderKind } from "../../shared/pruning-contracts";

import { WHITELIST_CATEGORIES, type NodeCategory } from "./whitelist";

/**
 * pruning 候補ノードに対する category dispatch の単一ソース。
 *
 * `NodeCategory` (入力分類 / whitelist) → 公開 API の `PlaceholderKind` と
 * 置換先 AST ノードを生成する `buildNode` の組を 1 行で対応付ける。
 * 新しい placeholder kind を追加する際の drift 面を 1 箇所に集約する目的。
 *
 * 判断: ai-guide/code-map.md (Pruning エンジン §置換操作の粒度)
 */
export interface CategoryReplacement {
  readonly placeholderKind: PlaceholderKind;
  readonly buildNode: (placeholderId: string) => Node;
}

const REPLACEMENTS: Record<NodeCategory, CategoryReplacement> = {
  statement: {
    placeholderKind: PLACEHOLDER_KIND.STATEMENT,
    buildNode: () => emptyStatement(),
  },
  identifier: {
    placeholderKind: PLACEHOLDER_KIND.IDENTIFIER,
    buildNode: (placeholderId) => identifier(sanitizeIdentifier(placeholderId)),
  },
  expression: {
    placeholderKind: PLACEHOLDER_KIND.EXPRESSION,
    buildNode: (placeholderId) => stringLiteral(placeholderId),
  },
};

/**
 * `node` の Babel 型から CategoryReplacement を引く。whitelist (`WHITELIST_CATEGORIES`) に無い
 * 型は候補対象外なので null。
 */
export function replacementFor(node: Node): CategoryReplacement | null {
  const category = WHITELIST_CATEGORIES.get(node.type);
  return category === undefined ? null : REPLACEMENTS[category];
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
