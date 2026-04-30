/** rules/: pruning 対象の宣言データ集 (whitelist / blacklist / replacement)。 */
export { WHITELIST_CATEGORIES, PARSER_PLUGINS, type NodeCategory } from "./whitelist";
export { BLACKLIST_CATEGORIES, type ExcludeRule, type GrammarBlacklist } from "./blacklist";
export { replacementFor, type CategoryReplacement } from "./replacement";
