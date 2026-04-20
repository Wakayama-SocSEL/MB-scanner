/**
 * checkException の代数的性質 (反射律・対称律) を property-based に検証する。
 */
import { describe, it } from "vitest";
import * as fc from "fast-check";
import { checkException } from "../../../src/equivalence-checker/oracles/exception";
import type { ExecutionCapture } from "../../../src/equivalence-checker/sandbox/executor";

function capture(overrides: Partial<ExecutionCapture> = {}): ExecutionCapture {
  return {
    return_value: "undefined",
    return_is_undefined: true,
    arg_snapshots: [],
    exception: null,
    console_log: [],
    new_globals: [],
    timed_out: false,
    ...overrides,
  };
}

const exceptionCapture = fc.option(
  fc.record({
    ctor: fc.constantFrom("Error", "TypeError", "RangeError", "SyntaxError"),
    message: fc.string({ maxLength: 20 }),
  }),
  { nil: null },
);

const arbitraryCapture = exceptionCapture.map((exception) => capture({ exception }));

describe("checkException (property)", () => {
  it("反射律: 自分自身との比較で not_equal は発生しない", () => {
    fc.assert(
      fc.property(arbitraryCapture, (cap) => {
        const v = checkException(cap, cap).verdict;
        return v !== "not_equal";
      }),
      { numRuns: 200 },
    );
  });

  it("対称律: slow/fast 入れ替えで verdict 不変", () => {
    fc.assert(
      fc.property(arbitraryCapture, arbitraryCapture, (a, b) => {
        return checkException(a, b).verdict === checkException(b, a).verdict;
      }),
      { numRuns: 200 },
    );
  });

  it("片方だけ例外は常に not_equal", () => {
    const withExc = fc
      .record({
        ctor: fc.constantFrom("Error", "TypeError"),
        message: fc.string({ maxLength: 10 }),
      })
      .map((exception) => capture({ exception }));
    const withoutExc = fc.constant(capture({ exception: null }));
    fc.assert(
      fc.property(withExc, withoutExc, (exc, noexc) => {
        return checkException(exc, noexc).verdict === "not_equal";
      }),
      { numRuns: 50 },
    );
  });
});
