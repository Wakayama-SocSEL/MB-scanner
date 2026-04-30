import type { ParserPlugin } from "@babel/parser";
import * as t from "@babel/types";

/**
 * pruning 対象となる Babel ノード型の分類テーブル (whitelist)。
 *
 * `@babel/types` の `Statement` / `Expression` alias から alias-driven に自動導出する
 * (ADR-0006)。データセット・dataset 言語に依存せず文法だけで決まる。
 *
 * 除外集合は本 ADR §機械的除外集合 で定義された 3 群:
 *   - 構造的 no-op: `PARSER_PLUGINS` で有効化していない plugin の型 (TS / JSX / Flow)
 *   - アルゴリズム不変条件: `EmptyStatement` (置換ターゲット自身)
 *   - 時点規範的除外: TC39 stage < 4 の experimental 構文
 *
 * カテゴリの意味:
 *   - statement: `EmptyStatement` に置換して削除する
 *   - expression: `"$Pn"` 文字列リテラル (式) に置換してワイルドカード化する
 *   - identifier: `$VAR` 識別子に置換してリネーム扱いにする
 *
 * 新しい placeholder kind の追加は `replacement.ts:REPLACEMENTS` を参照。
 */

export type NodeCategory = "statement" | "expression" | "identifier";

/**
 * pruning モジュールの parser plugin 設定。
 *
 * 対象言語は ECMAScript core (素 JS)。TS / JSX / Flow への拡張は ADR-0006 §対象言語拡張で
 * 扱える dataset 例 を参照し、本配列と下記の除外集合を paired で更新する (paired-change 原則)。
 * `parser.ts` はこの定数を使って `@babel/parser` を構成する。
 */
export const PARSER_PLUGINS: ReadonlyArray<ParserPlugin> = [];

const ENABLED_PLUGIN_NAMES = new Set<string>(
  PARSER_PLUGINS.map((p) => (typeof p === "string" ? p : p[0])),
);

/**
 * Flow 由来の構文型のうち prefix (`Declare`) で判定できないもの。
 */
const FLOW_EXPLICIT_TYPES = new Set([
  "TypeAlias",
  "OpaqueType",
  "InterfaceDeclaration",
  "EnumDeclaration",
  "TypeCastExpression",
]);

/**
 * 構造的 no-op: parser config で plugin OFF の構文型 → AST に出現不能 → whitelist 含有は
 * vacuous なので除外。`ENABLED_PLUGIN_NAMES` を変更すると除外範囲が自動で連動する
 * (paired-change の実装表現)。
 */
function isPluginExcluded(type: string): boolean {
  if (!ENABLED_PLUGIN_NAMES.has("typescript") && type.startsWith("TS")) return true;
  if (!ENABLED_PLUGIN_NAMES.has("jsx") && type.startsWith("JSX")) return true;
  if (!ENABLED_PLUGIN_NAMES.has("flow")) {
    if (type.startsWith("Declare")) return true;
    if (FLOW_EXPLICIT_TYPES.has(type)) return true;
  }
  return false;
}

/**
 * アルゴリズム不変条件: `EmptyStatement` は statement カテゴリの置換ターゲット
 * (`deleteStatement`) 自身。whitelist に入れると自己置換ループが発生する。
 */
const ALREADY_MINIMAL_TYPES = new Set(["EmptyStatement"]);

/**
 * 時点規範的除外: TC39 stage < 4 (= "Finished" 未到達) の experimental 構文。
 *
 * ADR-0006 Date (2026-04-27) 時点での TC39 提案 stage に基づく。Babel version は
 * `pnpm-lock.yaml` で pin されているため、AST 型集合は完全再現可能。stage 4 への昇格時には
 * 本リストから外す (ADR-0006 トリガー節)。各構文の stage は TC39 提案リポジトリで検証可能:
 * https://github.com/tc39/proposals
 */
const EXPERIMENTAL_TYPES = new Set([
  "BindExpression", // stage 0
  "DoExpression", // stage 1
  "RecordExpression", // stage 2 → withdrawn (2023)
  "TupleExpression", // stage 2 → withdrawn (2023)
  "ModuleExpression", // stage 1
  "PipelineBareFunction", // stage 2 (Hack proposal)
  "PipelinePrimaryTopicReference", // stage 2
  "PipelineTopicExpression", // stage 2
  "TopicReference", // stage 2
  "DecimalLiteral", // stage 1
]);

function isExcluded(type: string): boolean {
  return (
    isPluginExcluded(type) ||
    ALREADY_MINIMAL_TYPES.has(type) ||
    EXPERIMENTAL_TYPES.has(type)
  );
}

/**
 * `@babel/types` の alias テーブルからカテゴリ別 whitelist を構築する。
 *
 * カテゴリ振り分け規則 (ADR-0006):
 *   - `Identifier` 単独 → identifier (Expression alias にも属するが binding 位置除外を
 *     grammar-blacklist で扱うため独立。ADR-0005:71-77)
 *   - `FLIPPED_ALIAS_KEYS.Statement` ∖ excluded → statement
 *   - `FLIPPED_ALIAS_KEYS.Expression` ∖ {Identifier} ∖ excluded → expression
 */
function buildWhitelistCategories(): ReadonlyMap<string, NodeCategory> {
  const m = new Map<string, NodeCategory>();
  const flipped = (t as unknown as { FLIPPED_ALIAS_KEYS?: Record<string, string[]> })
    .FLIPPED_ALIAS_KEYS;
  if (flipped === undefined) {
    throw new Error(
      "@babel/types.FLIPPED_ALIAS_KEYS が未初期化です。Babel のメジャーバージョン更新で API が変わった可能性があります (ADR-0006 トリガー)",
    );
  }

  m.set("Identifier", "identifier");

  for (const type of flipped.Statement ?? []) {
    if (!isExcluded(type)) m.set(type, "statement");
  }
  for (const type of flipped.Expression ?? []) {
    if (type === "Identifier") continue;
    if (!isExcluded(type)) m.set(type, "expression");
  }

  return m;
}

export const WHITELIST_CATEGORIES: ReadonlyMap<string, NodeCategory> = buildWhitelistCategories();
