/**
 * 対象: src/pruning/rules/blacklist.ts (文法由来 blacklist 自動導出; ADR 0005)
 *
 * 観点:
 *   1. 方式 A (型 introspection) の snapshot test — 主要位置の除外ルールを固定値で pin
 *   2. 方式 A と方式 B (dry-run) のクロスチェック — Babel 内部 API の形式変化を
 *      `expect(A).toEqual(B)` で CI 検出する
 *   3. 起動時の smoke test — build 自体が落ちないこと
 *
 * 方式 B の probe 選定:
 *   - statement 候補の置換は EmptyStatement なので、EmptyStatement を probe に使う
 *     (Statement alias を受理する位置のみ通過する)
 *   - identifier/expression 候補は Identifier(`$VAR`) / StringLiteral(`$P0`) で置換されるが、
 *     それらは LVal / 特定リテラル列挙の位置でも個別に通ってしまう。
 *     目的は「Expression alias を受理する自由な式スロットか」を判定することなので、
 *     純 Expression (Expression alias のみに属する ThisExpression) を probe に使う。
 *     これが A の `CATEGORY_ALIAS.identifier = "Expression"` と対応する。
 */
import { describe, expect, it } from "vitest";
import * as t from "@babel/types";
import type { Node } from "@babel/types";

import {
  BLACKLIST_CATEGORIES,
  type ExcludeRule,
  type GrammarBlacklist,
} from "../../../src/pruning/rules/blacklist";
import { WHITELIST_CATEGORIES, type NodeCategory } from "../../../src/pruning/rules/whitelist";

describe("BLACKLIST_CATEGORIES — 方式 A snapshot (主要位置)", () => {
  const bl = BLACKLIST_CATEGORIES;

  // 置換後の型が受理されないなら、カテゴリを問わず true (無条件除外)
  const ALL_CATEGORIES: readonly NodeCategory[] = ["statement", "identifier", "expression"];

  function ruleAt(cat: NodeCategory, parent: string, key: string): ExcludeRule | undefined {
    return bl[cat].get(parent)?.get(key);
  }

  it("ForInStatement.left は全カテゴリで無条件除外", () => {
    for (const cat of ALL_CATEGORIES) {
      expect(ruleAt(cat, "ForInStatement", "left")).toBe(true);
    }
  });

  it("ForInStatement.right は identifier/expression では除外されない (Expression 受理)", () => {
    expect(ruleAt("identifier", "ForInStatement", "right")).toBeUndefined();
    expect(ruleAt("expression", "ForInStatement", "right")).toBeUndefined();
  });

  it("ForInStatement.body は statement では除外されない (Statement 受理)", () => {
    expect(ruleAt("statement", "ForInStatement", "body")).toBeUndefined();
  });

  it("AssignmentExpression.left は全カテゴリで無条件除外 (LVal 位置)", () => {
    for (const cat of ALL_CATEGORIES) {
      expect(ruleAt(cat, "AssignmentExpression", "left")).toBe(true);
    }
  });

  it("UpdateExpression.argument は identifier/expression では除外されない (文法上 Expression 受理)", () => {
    // 旧手書き blacklist との意図的 diff (ADR 0005 §既知の diff)
    expect(ruleAt("identifier", "UpdateExpression", "argument")).toBeUndefined();
    expect(ruleAt("expression", "UpdateExpression", "argument")).toBeUndefined();
    // statement は EmptyStatement 置換できないので除外
    expect(ruleAt("statement", "UpdateExpression", "argument")).toBe(true);
  });

  it("VariableDeclarator.id は identifier/expression で無条件除外、init は除外されない", () => {
    expect(ruleAt("identifier", "VariableDeclarator", "id")).toBe(true);
    expect(ruleAt("expression", "VariableDeclarator", "id")).toBe(true);
    expect(ruleAt("identifier", "VariableDeclarator", "init")).toBeUndefined();
    expect(ruleAt("expression", "VariableDeclarator", "init")).toBeUndefined();
  });

  it("MemberExpression.property は computed=false の条件で除外 (discriminator ルール)", () => {
    const rule = ruleAt("identifier", "MemberExpression", "property");
    expect(rule).toEqual({ discriminator: "computed", value: [false] });
    expect(ruleAt("expression", "MemberExpression", "property")).toEqual({
      discriminator: "computed",
      value: [false],
    });
  });

  it("ObjectProperty.key も computed=false の条件で除外", () => {
    expect(ruleAt("identifier", "ObjectProperty", "key")).toEqual({
      discriminator: "computed",
      value: [false],
    });
    expect(ruleAt("expression", "ObjectProperty", "key")).toEqual({
      discriminator: "computed",
      value: [false],
    });
  });

  it("ClassMethod.key / ObjectMethod.key も computed=false 条件で除外", () => {
    for (const parent of ["ClassMethod", "ObjectMethod", "ClassProperty"]) {
      expect(ruleAt("identifier", parent, "key")).toEqual({
        discriminator: "computed",
        value: [false],
      });
    }
  });

  it("CatchClause.param は identifier/expression で無条件除外 (binding 位置)", () => {
    expect(ruleAt("identifier", "CatchClause", "param")).toBe(true);
    expect(ruleAt("expression", "CatchClause", "param")).toBe(true);
  });

  it("FunctionDeclaration.id / params も無条件除外", () => {
    expect(ruleAt("identifier", "FunctionDeclaration", "id")).toBe(true);
    expect(ruleAt("identifier", "FunctionDeclaration", "params")).toBe(true);
    expect(ruleAt("identifier", "ArrowFunctionExpression", "params")).toBe(true);
  });

  it("LabeledStatement.label / BreakStatement.label / ContinueStatement.label は無条件除外", () => {
    expect(ruleAt("identifier", "LabeledStatement", "label")).toBe(true);
    expect(ruleAt("identifier", "BreakStatement", "label")).toBe(true);
    expect(ruleAt("identifier", "ContinueStatement", "label")).toBe(true);
  });

  it("RestElement.argument / ArrayPattern.elements / ObjectPattern.properties も除外 (destructuring LVal)", () => {
    // 旧手書き blacklist には無かったが、自動導出では除外される (plan §226 で想定)
    expect(ruleAt("identifier", "RestElement", "argument")).toBe(true);
    expect(ruleAt("identifier", "ArrayPattern", "elements")).toBe(true);
    expect(ruleAt("identifier", "ObjectPattern", "properties")).toBe(true);
  });
});

describe("BLACKLIST_CATEGORIES — 方式 B (dry-run) との cross-check", () => {
  /**
   * Babel 内部の特殊実装で A (introspection) と B (dry-run) が乖離する既知の型は
   * cross-check から除外する。これらは候補 enumerate の主要経路ではなく、かつ
   * 「Babel の validator 実装形式が変わったら検出」というテスト目的は他の主要
   * 位置で達成できる:
   *
   *   - `File`: comments / tokens が `assertEach` 素 (chainOf 非使用) で、非配列
   *     probe を渡すと早期 return → B は常に accept するが、A は `each` 内部を
   *     introspection して blacklist する
   *   - `BindExpression` (stage-1 experimental): 非 8_BREAKING モードでは validate
   *     が no-op `() => {}` に `oneOfNodeTypes` property だけ付与される形で、B は
   *     常に accept、A は introspection で blacklist
   *   - `OptionalMemberExpression` / `OptionalCallExpression`: `property` 等の
   *     validator が `node.computed` を参照する手動 discriminator 実装で、
   *     unionShape メタを持たない。B は computed=undefined で振る舞いが違う
   */
  const CROSSCHECK_SKIP_PARENTS = new Set([
    "File",
    "BindExpression",
    "OptionalMemberExpression",
    "OptionalCallExpression",
  ]);

  it("方式 A と方式 B の出力が既知の差分を除いて一致する", () => {
    const a = normalizeFiltered(BLACKLIST_CATEGORIES, CROSSCHECK_SKIP_PARENTS);
    const b = normalizeFiltered(buildByDryRun(), CROSSCHECK_SKIP_PARENTS);
    expect(a).toEqual(b);
  });
});

describe("BLACKLIST_CATEGORIES — 構造 smoke", () => {
  it("WHITELIST_CATEGORIES の全カテゴリがキーに含まれる", () => {
    for (const cat of new Set(WHITELIST_CATEGORIES.values())) {
      expect(BLACKLIST_CATEGORIES[cat]).toBeInstanceOf(Map);
    }
  });
});

/**
 * 方式 B: dry-run ベースの独立ヘルパ。
 * 各位置に probe を差し込んで validator に受理されるか実測し、blacklist を再構築する。
 * A (type introspection) と独立なので、Babel 内部 API の形式変化 (例:
 * `oneOfNodeTypes` が別名にリネームされる) は本テストで CI 検出できる。
 *
 * Probe 選定 (上の docstring 参照):
 *   - statement → EmptyStatement (Statement alias のみ)
 *   - identifier/expression → ThisExpression (Expression alias のみ、LVal 等に属さない)
 */
function buildByDryRun(): GrammarBlacklist {
  const probes: Readonly<Record<NodeCategory, Node>> = {
    statement: t.emptyStatement(),
    identifier: t.thisExpression(),
    expression: t.thisExpression(),
  };

  const byCategory: Record<NodeCategory, Map<string, Map<string, ExcludeRule>>> = {
    statement: new Map(),
    identifier: new Map(),
    expression: new Map(),
  };

  const nodeFields = t.NODE_FIELDS;
  const unionShapes = (t as unknown as {
    NODE_UNION_SHAPES__PRIVATE?: Record<string, UnionShapeShape>;
  }).NODE_UNION_SHAPES__PRIVATE ?? {};

  for (const parentType of Object.keys(nodeFields)) {
    const fields = nodeFields[parentType];
    if (fields === undefined) continue;
    const union = unionShapes[parentType];

    for (const key of Object.keys(fields)) {
      const field = fields[key];
      if (field === undefined || field.validate === undefined) continue;

      const unionKeyShape = union?.shapes.find((s) => s.properties[key] !== undefined);
      if (union !== undefined && unionKeyShape !== undefined) {
        for (const cat of Object.keys(byCategory) as NodeCategory[]) {
          const blacklistValues: unknown[] = [];
          for (const shape of union.shapes) {
            const shapeField = shape.properties[key];
            if (shapeField === undefined || shapeField.validate === undefined) continue;
            const parent = {
              type: parentType,
              [union.discriminator]: shape.value[0],
            };
            if (!tryAcceptedBy(shapeField.validate as unknown as ValidatorLike, parent, key, probes[cat])) {
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
          addRule(byCategory[cat], parentType, key, rule);
        }
      } else {
        const parent = { type: parentType };
        for (const cat of Object.keys(byCategory) as NodeCategory[]) {
          if (!tryAcceptedBy(field.validate as unknown as ValidatorLike, parent, key, probes[cat])) {
            addRule(byCategory[cat], parentType, key, true);
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

interface ValidatorLike {
  readonly chainOf?: readonly ValidatorLike[];
  readonly each?: ValidatorLike;
  readonly type?: string;
  (node: unknown, key: string, val: unknown): void;
}

interface UnionShapeShape {
  readonly discriminator: string;
  readonly shapes: ReadonlyArray<{
    readonly value: readonly unknown[];
    readonly properties: Readonly<Record<string, { readonly validate?: unknown }>>;
  }>;
}

/**
 * 配列フィールドなら中身の each validator を使って単一要素を検証し、
 * スカラフィールドなら直接 probe を渡して検証する。
 */
function tryAcceptedBy(
  validate: ValidatorLike,
  parent: object,
  key: string,
  probe: Node,
): boolean {
  let actual: ValidatorLike = validate;
  if (validate.chainOf !== undefined && validate.chainOf[0]?.type === "array") {
    const eachValidator = validate.chainOf.find((c) => c.each !== undefined);
    if (eachValidator?.each !== undefined) actual = eachValidator.each;
  }
  try {
    actual(parent, key, probe);
    return true;
  } catch {
    return false;
  }
}

function addRule(
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

/** toEqual 比較のため、ネスト Map を plain object に落とす (skip parents を除外)。 */
function normalizeFiltered(
  bl: GrammarBlacklist,
  skipParents: ReadonlySet<string>,
): Record<NodeCategory, Record<string, Record<string, ExcludeRule>>> {
  const out = {
    statement: {} as Record<string, Record<string, ExcludeRule>>,
    identifier: {} as Record<string, Record<string, ExcludeRule>>,
    expression: {} as Record<string, Record<string, ExcludeRule>>,
  };
  for (const cat of ["statement", "identifier", "expression"] as const) {
    for (const [parent, inner] of bl[cat]) {
      if (skipParents.has(parent)) continue;
      const obj: Record<string, ExcludeRule> = {};
      for (const [key, rule] of inner) {
        obj[key] = rule;
      }
      out[cat][parent] = obj;
    }
  }
  return out;
}
