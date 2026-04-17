import { describe, expect, it } from "vitest";
import { checkEquivalence } from "../../src/equivalence-checker/checker";

describe("checkEquivalence", () => {
  it("equivalent な式は equal verdict", async () => {
    const result = await checkEquivalence({ slow: "1 + 1", fast: "2" });
    expect(result.verdict).toBe("equal");
    const returnValue = result.observations.find((o) => o.oracle === "return_value");
    expect(returnValue?.verdict).toBe("equal");
  });

  it("x % 2 vs x & 1 は負数で not_equal（Selakovic #8 の反例）", async () => {
    const result = await checkEquivalence({
      setup: "const x = -3;",
      slow: "x % 2",
      fast: "x & 1",
    });
    expect(result.verdict).toBe("not_equal");
    const ret = result.observations.find((o) => o.oracle === "return_value");
    expect(ret?.verdict).toBe("not_equal");
  });

  it("両側 throw (ctor + msg 一致) は equal", async () => {
    const result = await checkEquivalence({
      slow: `throw new TypeError("boom")`,
      fast: `throw new TypeError("boom")`,
    });
    expect(result.verdict).toBe("equal");
    const exc = result.observations.find((o) => o.oracle === "exception");
    expect(exc?.verdict).toBe("equal");
  });

  it("片方だけ throw は not_equal", async () => {
    const result = await checkEquivalence({
      slow: "1",
      fast: `throw new Error("x")`,
    });
    expect(result.verdict).toBe("not_equal");
  });

  it("setup で配列 + 両側が等価な変異 → equal", async () => {
    const result = await checkEquivalence({
      setup: "const arr = [1, 2, 3];",
      slow: "arr.push(4); arr",
      fast: "arr[arr.length] = 4; arr",
    });
    expect(result.verdict).toBe("equal");
  });

  it("console 出力が異なると not_equal", async () => {
    const result = await checkEquivalence({
      slow: `console.log("a")`,
      fast: `console.log("b")`,
    });
    expect(result.verdict).toBe("not_equal");
  });

  it("slow と fast は副作用を共有しない", async () => {
    // slow 側が配列を破壊しても、fast 側には伝播しない
    const result = await checkEquivalence({
      setup: "const arr = [1, 2, 3];",
      slow: "arr.pop(); arr.length",
      fast: "arr.length",
    });
    // slow は 2, fast は 3
    expect(result.verdict).toBe("not_equal");
  });

  it("timeout → error", async () => {
    const result = await checkEquivalence({
      slow: "while(true){}",
      fast: "1",
      timeout_ms: 50,
    });
    expect(result.verdict).toBe("not_equal"); // 片方 timeout 例外、片方正常 → O3 で not_equal
  });

  it("4 observation が必ず揃う", async () => {
    const result = await checkEquivalence({ slow: "1", fast: "1" });
    expect(result.observations.map((o) => o.oracle)).toEqual([
      "return_value",
      "argument_mutation",
      "exception",
      "external_observation",
    ]);
  });
});
