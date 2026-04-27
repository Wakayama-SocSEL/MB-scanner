import type { Node } from "@babel/types";

import { PLACEHOLDER_KIND, type PlaceholderKind } from "../shared/types";

import type { ReplacementMode } from "./ast/replace";
import { NODE_CATEGORY, type NodeCategory } from "./constants";

/**
 * pruning 候補ノードに対する category dispatch の単一ソース。
 *
 * `NodeCategory` (入力分類 / whitelist) → 内部の `ReplacementMode` (replace.ts の
 * 置換アルゴリズム選択) と公開 API の `PlaceholderKind` (Placeholder.kind) を 1 行で
 * 対応付ける。新しい placeholder kind を追加する際の drift 面を 1 箇所に集約する目的。
 *
 * 内部 mode と公開 kind を別の型に保つ理由は ai-guide/code-map.md 参照: 将来「同じ
 * PlaceholderKind に複数 mode (例: statement に deleteStatement と wildcardStatement)」が
 * 必要になった際、ReplacementMode 側だけ枝分かれさせられる余地を残す。
 */
export interface CategoryHandler {
  readonly mode: ReplacementMode;
  readonly placeholderKind: PlaceholderKind;
}

const HANDLERS: Record<NodeCategory, CategoryHandler> = {
  statement: { mode: "deleteStatement", placeholderKind: PLACEHOLDER_KIND.STATEMENT },
  identifier: { mode: "wildcardIdentifier", placeholderKind: PLACEHOLDER_KIND.IDENTIFIER },
  expression: { mode: "wildcardExpression", placeholderKind: PLACEHOLDER_KIND.EXPRESSION },
};

/**
 * `node` の Babel 型から CategoryHandler を引く。whitelist (`NODE_CATEGORY`) に無い
 * 型は候補対象外なので null。
 */
export function handlerForNode(node: Node): CategoryHandler | null {
  const category = NODE_CATEGORY.get(node.type);
  return category === undefined ? null : HANDLERS[category];
}
