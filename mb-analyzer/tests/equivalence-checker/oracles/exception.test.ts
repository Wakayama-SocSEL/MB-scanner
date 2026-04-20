/**
 * 対象: Oracle O3 - checkException (exception)
 * 観点: 両側の throw 状況と例外の ctor + message を比較する
 * 判定事項:
 *   - 両側とも正常終了 → not_applicable
 *   - 両側例外かつ ctor と message が一致 → equal
 *   - 両側例外だが ctor か message が異なる → not_equal
 *   - 片方だけ例外 → not_equal
 */
import { describe, expect, it } from "vitest";
import { checkException } from "../../../src/equivalence-checker/oracles/exception";
import type { ExceptionCapture, ExecutionCapture } from "../../../src/equivalence-checker/sandbox/executor";

function capture(exception: ExceptionCapture | null): ExecutionCapture {
  return {
    return_value: "undefined",
    return_is_undefined: true,
    arg_snapshots: [],
    exception,
    console_log: [],
    new_globals: [],
    timed_out: false,
  };
}

describe("checkException", () => {
  it("両側正常終了 → not_applicable", () => {
    expect(checkException(capture(null), capture(null)).verdict).toBe("not_applicable");
  });

  it("ctor + message 一致 → equal", () => {
    const e = { ctor: "TypeError", message: "x" };
    expect(checkException(capture(e), capture(e)).verdict).toBe("equal");
  });

  it("ctor 不一致 → not_equal", () => {
    const s = capture({ ctor: "TypeError", message: "x" });
    const f = capture({ ctor: "RangeError", message: "x" });
    const obs = checkException(s, f);
    expect(obs.verdict).toBe("not_equal");
    expect(obs.detail).toContain("TypeError");
  });

  it("message 不一致 → not_equal", () => {
    const s = capture({ ctor: "Error", message: "a" });
    const f = capture({ ctor: "Error", message: "b" });
    expect(checkException(s, f).verdict).toBe("not_equal");
  });

  it("片方だけ例外 → not_equal", () => {
    const obs = checkException(capture({ ctor: "Error", message: "x" }), capture(null));
    expect(obs.verdict).toBe("not_equal");
    expect(obs.detail).toContain("only slow");
  });
});
