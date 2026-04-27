/**
 * pruning 対象となる Babel ノード型の分類テーブル。
 *
 * ast/candidates.ts は keys を whitelist として使い、engine.ts は category から
 * 置換モードを決める。分類を 1 箇所に集約することで、新しい型を対象に加えたときの
 * drift (候補には入ったがモード選択が未対応、など) を防ぐ。
 *
 * 分類の意味:
 *   - statement: EmptyStatement に置換して削除する
 *   - expression: `"$Pn"` 文字列リテラル (式) に置換してワイルドカード化する
 *   - identifier: `$VAR` 識別子に置換してリネーム扱いにする
 */

export type NodeCategory = "statement" | "expression" | "identifier";

export const NODE_CATEGORY: ReadonlyMap<string, NodeCategory> = new Map([
  // Statements
  ["IfStatement", "statement"],
  ["ExpressionStatement", "statement"],
  ["VariableDeclaration", "statement"],
  ["BlockStatement", "statement"],
  ["ReturnStatement", "statement"],
  ["ThrowStatement", "statement"],
  // Identifiers
  ["Identifier", "identifier"],
  // Expressions (literals + composite)
  ["NumericLiteral", "expression"],
  ["StringLiteral", "expression"],
  ["BooleanLiteral", "expression"],
  ["NullLiteral", "expression"],
  ["RegExpLiteral", "expression"],
  ["TemplateLiteral", "expression"],
  ["MemberExpression", "expression"],
  ["CallExpression", "expression"],
  ["NewExpression", "expression"],
  ["BinaryExpression", "expression"],
  ["LogicalExpression", "expression"],
  ["UnaryExpression", "expression"],
  ["UpdateExpression", "expression"],
  ["AssignmentExpression", "expression"],
  ["ConditionalExpression", "expression"],
  ["ObjectExpression", "expression"],
  ["ArrayExpression", "expression"],
]);
