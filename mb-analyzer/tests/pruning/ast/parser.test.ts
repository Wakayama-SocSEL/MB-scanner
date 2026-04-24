/**
 * 対象: src/pruning/ast/parser.ts (Babel parse ラッパ)
 * 観点: 関数外 return / 空文字列 / syntax error / TS 構文 / 大きなコードで意図通りの挙動
 * 判定事項:
 *   - 正常なスニペットは t.File を返し、program.body が取り出せる
 *   - 空文字列は空の body を持つ File として返る (エラーにしない)
 *   - 関数外 return / await / super も許容
 *   - TypeScript 構文 (型アノテーション) も parse できる
 *   - syntax error は SyntaxError として伝播する
 */
import { describe, expect, it } from "vitest";
import { parse } from "../../../src/pruning/ast/parser";

describe("parse", () => {
  it("式を含むスニペットを File として parse する", () => {
    const file = parse("const x = arr[0];");
    expect(file.type).toBe("File");
    expect(file.program.body).toHaveLength(1);
    expect(file.program.body[0]?.type).toBe("VariableDeclaration");
  });

  it("空文字列は空 body を持つ File を返す", () => {
    const file = parse("");
    expect(file.type).toBe("File");
    expect(file.program.body).toHaveLength(0);
  });

  it("関数外の return も許容する (pruning 対象スニペット向け)", () => {
    const file = parse("return arr[0];");
    expect(file.program.body[0]?.type).toBe("ReturnStatement");
  });

  it("関数外の await も許容する", () => {
    const file = parse("await fetch(url);");
    expect(file.program.body[0]?.type).toBe("ExpressionStatement");
  });

  it("TypeScript の型アノテーションも parse できる", () => {
    const file = parse("const x: number = 1;");
    expect(file.program.body[0]?.type).toBe("VariableDeclaration");
  });

  it("JSX も parse できる", () => {
    const file = parse("const el = <div>hi</div>;");
    expect(file.program.body[0]?.type).toBe("VariableDeclaration");
  });

  it("syntax error は SyntaxError として投げる", () => {
    expect(() => parse("const x =")).toThrow(SyntaxError);
  });

  it("複数文を parse して順序を保つ", () => {
    const file = parse("const a = 1; const b = 2; a + b;");
    expect(file.program.body).toHaveLength(3);
    expect(file.program.body.map((n) => n.type)).toEqual([
      "VariableDeclaration",
      "VariableDeclaration",
      "ExpressionStatement",
    ]);
  });
});
