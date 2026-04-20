/**
 * 対象: Oracle O2 - checkArgumentMutation (argument-mutation)
 * 観点: setup 由来の object/array に対する pre/post snapshot の差分を両側で比較する
 * 判定事項:
 *   - 両側とも setup で object/array を 1 つも定義していない → not_applicable
 *   - snapshot の pre/post にシリアライズ不能マーカを含む → error
 *   - key 集合と各 key の post が一致 → equal
 *   - いずれかの key で post が異なる → not_equal（detail に差分 key を列挙）
 */
import { describe, expect, it } from "vitest";
import { checkArgumentMutation } from "../../../src/equivalence-checker/oracles/argument-mutation";
import type { ExecutionCapture } from "../../../src/equivalence-checker/sandbox/executor";
import { UNSERIALIZABLE_MARKER } from "../../../src/equivalence-checker/sandbox/executor";

function capture(snapshots: ExecutionCapture["arg_snapshots"]): ExecutionCapture {
  return {
    return_value: "undefined",
    return_is_undefined: true,
    arg_snapshots: snapshots,
    exception: null,
    console_log: [],
    new_globals: [],
    timed_out: false,
  };
}

describe("checkArgumentMutation", () => {
  it("setup で object 無し → not_applicable", () => {
    expect(checkArgumentMutation(capture([]), capture([])).verdict).toBe("not_applicable");
  });

  it("同じ key で同じ post → equal", () => {
    const s = capture([{ key: "arr", pre: "[1,2]", post: "[1,2,3]" }]);
    const f = capture([{ key: "arr", pre: "[1,2]", post: "[1,2,3]" }]);
    expect(checkArgumentMutation(s, f).verdict).toBe("equal");
  });

  it("同じ key で post が異なる → not_equal", () => {
    const s = capture([{ key: "arr", pre: "[1,2]", post: "[1,2,3]" }]);
    const f = capture([{ key: "arr", pre: "[1,2]", post: "[1,2]" }]);
    const obs = checkArgumentMutation(s, f);
    expect(obs.verdict).toBe("not_equal");
    expect(obs.detail).toContain("arr");
  });

  it("key 集合が違う → not_equal", () => {
    const s = capture([{ key: "a", pre: "{}", post: "{}" }]);
    const f = capture([{ key: "b", pre: "{}", post: "{}" }]);
    expect(checkArgumentMutation(s, f).verdict).toBe("not_equal");
  });

  it("UNSERIALIZABLE_MARKER を含む → error", () => {
    const s = capture([{ key: "c", pre: UNSERIALIZABLE_MARKER, post: "[]" }]);
    const f = capture([{ key: "c", pre: "[]", post: "[]" }]);
    expect(checkArgumentMutation(s, f).verdict).toBe("error");
  });
});
