import { parse as babelParse } from "@babel/parser";
import type { File } from "@babel/types";

/**
 * JS/TS スニペットを Babel で parse して ``t.File`` を返す薄いラッパ。
 *
 * pruning 対象として渡されるコードは関数本体やヒューリスティックに切り出された断片が多く、
 * ``return`` や ``await`` が関数の外に現れる可能性があるため ``allowReturnOutsideFunction``
 * / ``allowAwaitOutsideFunction`` を有効にする。
 *
 * エラー時は Babel が投げる ``SyntaxError`` をそのまま呼び出し側 (pruning engine) に伝播させる。
 * 本 PR では API のみ提供し、engine 側の catch は PR #2 で実装する。
 */
export function parse(code: string): File {
  return babelParse(code, {
    sourceType: "module",
    allowReturnOutsideFunction: true,
    allowAwaitOutsideFunction: true,
    allowSuperOutsideMethod: true,
    allowUndeclaredExports: true,
    errorRecovery: false,
    plugins: ["typescript", "jsx"],
  });
}
