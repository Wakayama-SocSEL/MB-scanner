import generateModule from "@babel/generator";
import { parse as babelParse } from "@babel/parser";
import type { File, Node } from "@babel/types";

import { PARSER_PLUGINS } from "../constants";

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
    // plugin 集合は constants.ts の PARSER_PLUGINS で一元管理する (ADR-0006 paired-change)。
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
