import generateModule from "@babel/generator";
import { parse as babelParse } from "@babel/parser";
import type { File, Node } from "@babel/types";

import { PARSER_PLUGINS } from "../rules/whitelist";

/**
 * JS/TS スニペットを Babel で parse して File AST を返す。
 *
 * pruning 対象は関数本体やヒューリスティックで切り出された断片が多いので、
 * 関数外の `return` / `await` / `super` / `export` を許容する設定で parse する。
 * 失敗時は Babel の `SyntaxError` がそのまま throw される (errorRecovery なし)。
 */
export function parse(code: string): File {
  return babelParse(code, {
    sourceType: "module",
    allowReturnOutsideFunction: true,
    allowAwaitOutsideFunction: true,
    allowSuperOutsideMethod: true,
    allowUndeclaredExports: true,
    errorRecovery: false,
    // plugin 集合は rules/whitelist.ts の PARSER_PLUGINS で一元管理する (ADR-0006 paired-change)。
    // 現状は素 JS のみ。TS / JSX / Flow への拡張は ADR-0006 §対象言語拡張を参照。
    plugins: [...PARSER_PLUGINS],
  });
}

/**
 * `@babel/generator` の ESM / CJS wrapper 差を吸収して取得する。
 * `default` がある環境とない環境がある (bundler / runtime の組み合わせで分岐)。
 */
function resolveGenerator(): typeof generateModule {
  return (generateModule as unknown as { default?: typeof generateModule }).default ?? generateModule;
}

/**
 * File AST を JS/TS コード文字列に generate する。`parse` の対称関数。
 */
export function generate(file: File): string {
  return resolveGenerator()(file).code;
}

/**
 * 任意の Node を generate する。`generate(file)` は File 専用なので、Node 単独を
 * generate したいケース (snippetOfNode の fallback 等) で使う。失敗時は空文字。
 */
export function tryGenerateNode(node: Node): string {
  try {
    return resolveGenerator()(node).code;
  } catch {
    return "";
  }
}

// 判断: ai-guide/adr/0007-in-source-testing-internal-helpers.md
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;

  describe("parse (in-source)", () => {
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

    it("TypeScript の型アノテーションは SyntaxError (ADR-0006: 対象は素 JS)", () => {
      expect(() => parse("const x: number = 1;")).toThrow(SyntaxError);
    });

    it("JSX も SyntaxError (ADR-0006: 対象は素 JS)", () => {
      expect(() => parse("const el = <div>hi</div>;")).toThrow(SyntaxError);
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
}
