/** rules/: pruning 対象の宣言データ集 (whitelist / blacklist / replacement)。 */
export { NODE_CATEGORY, PARSER_PLUGINS, type NodeCategory } from "./whitelist";
export { getGrammarBlacklist, type ExcludeRule, type GrammarBlacklist } from "./blacklist";
export { replacementFor, type CategoryReplacement } from "./replacement";
