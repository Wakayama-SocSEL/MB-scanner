import * as t from "@babel/types";

import { WHITELIST_CATEGORIES, type NodeCategory } from "./whitelist";

/**
 * 候補位置の除外ルールを `@babel/types` の文法メタデータから導出する。
 *
 * 出力は (category → parent 型 → 親から見た子 key → 除外ルール) の 3 段 Map。
 * module load 時に 1 回だけ構築する (whitelist と対称)。
 *
 * 判断: ai-guide/adr/0005-grammar-derived-blacklist.md
 */

/**
 * 位置除外ルール。
 * - `true`: 無条件に除外
 * - `{ discriminator, value }`: 親の `discriminator` フィールド値が `value` のいずれかと
 *   一致したときに限り除外 (例: `{ discriminator: "computed", value: [false] }` は
 *   `obj.x` のような computed=false の位置でだけ効かせる)
 */
export type ExcludeRule =
  | true
  | { readonly discriminator: string; readonly value: readonly unknown[] };

export type CategoryBlacklist = ReadonlyMap<
  string,
  ReadonlyMap<string, ExcludeRule>
>;

export type GrammarBlacklist = Readonly<Record<NodeCategory, CategoryBlacklist>>;

/**
 * 候補カテゴリが受理されるために親 validator の `oneOfNodeTypes` に含まれていなければ
 * ならない alias 名。identifier→`Expression` の対応付けは binding 位置を L1 で除外する
 * ための grammar-level proxy (選択根拠は ADR-0005)。
 */
const CATEGORY_ALIAS: Readonly<Record<NodeCategory, string>> = {
  statement: "Statement",
  identifier: "Expression",
  expression: "Expression",
};

/** `@babel/types` の validator introspection プロパティの minimum subset。 */
interface ValidatorLike {
  readonly oneOfNodeTypes?: readonly string[];
  readonly oneOfNodeOrValueTypes?: readonly string[];
  readonly chainOf?: readonly ValidatorLike[];
  readonly each?: ValidatorLike;
  readonly type?: string;
}

interface UnionShape {
  readonly discriminator: string;
  readonly shapes: ReadonlyArray<{
    readonly name: string;
    readonly value: readonly unknown[];
    readonly properties: Readonly<Record<string, { readonly validate?: ValidatorLike }>>;
  }>;
}

/** `NODE_FIELDS[type][key].validate` から許容ノード型名の集合を再帰抽出する。 */
function extractAllowedTypes(validate: ValidatorLike | undefined): Set<string> {
  const out = new Set<string>();
  if (validate === undefined) return out;
  const stack: ValidatorLike[] = [validate];
  while (stack.length > 0) {
    const v = stack.pop();
    if (v === undefined) continue;
    if (v.oneOfNodeTypes) for (const n of v.oneOfNodeTypes) out.add(n);
    if (v.oneOfNodeOrValueTypes) for (const n of v.oneOfNodeOrValueTypes) out.add(n);
    if (v.chainOf) for (const c of v.chainOf) stack.push(c);
    if (v.each) stack.push(v.each);
  }
  return out;
}

function isCategoryAccepted(allowed: ReadonlySet<string>, category: NodeCategory): boolean {
  return allowed.has(CATEGORY_ALIAS[category]);
}

const ALL_CATEGORIES: readonly NodeCategory[] = Array.from(
  new Set(WHITELIST_CATEGORIES.values()),
);

function buildGrammarBlacklist(): GrammarBlacklist {
  const byCategory: Record<NodeCategory, Map<string, Map<string, ExcludeRule>>> = {
    statement: new Map(),
    identifier: new Map(),
    expression: new Map(),
  };

  const nodeFields = t.NODE_FIELDS;
  // NODE_UNION_SHAPES__PRIVATE は .d.ts の top-level 型定義に含まれない semi-public。
  const unionShapes = (t as unknown as { NODE_UNION_SHAPES__PRIVATE?: Record<string, UnionShape> })
    .NODE_UNION_SHAPES__PRIVATE ?? {};

  for (const parentType of Object.keys(nodeFields)) {
    const fields = nodeFields[parentType];
    if (fields === undefined) continue;
    const union = unionShapes[parentType];

    for (const key of Object.keys(fields)) {
      const field = fields[key];
      if (field === undefined || field.validate === undefined) continue;

      const unionKeyShape = union?.shapes.find((s) => s.properties[key] !== undefined);
      if (union !== undefined && unionKeyShape !== undefined) {
        // unionShape で分岐する key: shape ごとに category 受理を判定し、blacklist 側の
        // discriminator 値を集めてルール化する。全 shape で blacklist なら条件式に落とさず `true`。
        for (const cat of ALL_CATEGORIES) {
          const blacklistValues: unknown[] = [];
          for (const shape of union.shapes) {
            const shapeField = shape.properties[key];
            if (shapeField === undefined) continue;
            const allowed = extractAllowedTypes(shapeField.validate);
            if (!isCategoryAccepted(allowed, cat)) {
              blacklistValues.push(...shape.value);
            }
          }
          if (blacklistValues.length === 0) continue;
          const totalValues = union.shapes.flatMap((s) =>
            s.properties[key] !== undefined ? [...s.value] : [],
          );
          const rule: ExcludeRule =
            blacklistValues.length === totalValues.length
              ? true
              : { discriminator: union.discriminator, value: blacklistValues };
          setRule(byCategory[cat], parentType, key, rule);
        }
      } else {
        const allowed = extractAllowedTypes(field.validate as unknown as ValidatorLike);
        for (const cat of ALL_CATEGORIES) {
          if (!isCategoryAccepted(allowed, cat)) {
            setRule(byCategory[cat], parentType, key, true);
          }
        }
      }
    }
  }

  return {
    statement: byCategory.statement,
    identifier: byCategory.identifier,
    expression: byCategory.expression,
  };
}

function setRule(
  map: Map<string, Map<string, ExcludeRule>>,
  parentType: string,
  key: string,
  rule: ExcludeRule,
): void {
  let inner = map.get(parentType);
  if (inner === undefined) {
    inner = new Map();
    map.set(parentType, inner);
  }
  inner.set(key, rule);
}

export const BLACKLIST_CATEGORIES: GrammarBlacklist = buildGrammarBlacklist();
