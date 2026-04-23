/**
 * 対象: src/pruning/ast/diff.ts の SubtreeDiff と canonicalHash
 * 観点: ランダムな式について「同じソースから作った 2 つの AST は全サブツリーが common」を検証
 * 判定事項:
 *   - 同一ソースから生成した 2 つの File は互いに SubtreeDiff で全サブツリー common
 *   - 同一ソースの canonicalHash は等しい (決定性)
 *   - リテラル値を 1 箇所変えると File レベル hash が変わる
 */
import * as fc from "fast-check";
import { describe, it } from "vitest";
import { SubtreeDiff, canonicalHash } from "../../../src/pruning/ast/diff";
import { parse } from "../../../src/pruning/ast/parser";
import { walkAllNodes } from "./walk";

// 識別子・リテラル・演算子・構造を混ぜた短い JS 断片を生成する arbitrary。
// 再帰的に式を組み立て、pruning 対象として現実的な分布に寄せる。
const identifierArb: fc.Arbitrary<string> = fc.constantFrom("a", "b", "obj", "arr", "key", "x");
const numberArb: fc.Arbitrary<string> = fc.integer({ min: 0, max: 3 }).map((n) => String(n));
const stringArb: fc.Arbitrary<string> = fc
  .constantFrom("a", "b", "c")
  .map((s) => JSON.stringify(s));

const expressionArb: fc.Arbitrary<string> = fc.letrec((tie) => ({
  expr: fc.oneof(
    { depthSize: "small", withCrossShrink: true },
    identifierArb,
    numberArb,
    stringArb,
    fc
      .tuple(tie("expr") as fc.Arbitrary<string>, tie("expr") as fc.Arbitrary<string>)
      .map(([l, r]) => `(${l} + ${r})`),
    fc
      .tuple(tie("expr") as fc.Arbitrary<string>, tie("expr") as fc.Arbitrary<string>)
      .map(([o, p]) => `${o}[${p}]`),
    (tie("expr") as fc.Arbitrary<string>).map((e) => `!${e}`),
  ),
})).expr;

describe("SubtreeDiff (property)", () => {
  it("同じソースから作った 2 つの File は全サブツリーが common", () => {
    fc.assert(
      fc.property(expressionArb, (code) => {
        const slow = parse(code);
        const fast = parse(code);
        const diff = new SubtreeDiff(slow, fast);
        for (const node of walkAllNodes(slow)) {
          if (!diff.isCommon(node)) return false;
        }
        return true;
      }),
      { numRuns: 200 },
    );
  });

  it("canonicalHash は決定論的 (同じコード → 同じ hash)", () => {
    fc.assert(
      fc.property(expressionArb, (code) => {
        const h1 = canonicalHash(parse(code));
        const h2 = canonicalHash(parse(code));
        return h1 === h2;
      }),
      { numRuns: 200 },
    );
  });

  it("リテラル値を別の値に変えると File レベルの hash は変わる", () => {
    const codeArb = fc.tuple(identifierArb, numberArb, numberArb).filter(([, a, b]) => a !== b);
    fc.assert(
      fc.property(codeArb, ([name, a, b]) => {
        const h1 = canonicalHash(parse(`${name}[${a}]`));
        const h2 = canonicalHash(parse(`${name}[${b}]`));
        return h1 !== h2;
      }),
      { numRuns: 100 },
    );
  });
});
