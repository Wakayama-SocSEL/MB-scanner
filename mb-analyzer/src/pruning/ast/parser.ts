import { parse as babelParse } from "@babel/parser";
import type { File } from "@babel/types";

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
    plugins: ["typescript", "jsx"],
  });
}
