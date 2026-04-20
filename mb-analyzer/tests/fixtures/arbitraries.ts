/**
 * property テスト全般で共有する fast-check arbitrary 群。
 * sampling 空間が oracle の挙動に無関係な「汎用入力生成器」を一元化する。
 * 特定テストだけに必要な狭い分布はテストファイル内で定義するのが原則。
 */
import * as fc from "fast-check";

export const exceptionArbitrary = fc.option(
  fc.record({
    ctor: fc.constantFrom("Error", "TypeError", "RangeError", "SyntaxError"),
    message: fc.string({ maxLength: 20 }),
  }),
  { nil: null },
);
