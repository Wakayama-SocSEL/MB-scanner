import { describe, expect, it } from "vitest";
import vm from "node:vm";
import { createStabilizedContext, FROZEN_EPOCH_MS } from "../../../src/equivalence-checker/sandbox/stabilizer";

describe("createStabilizedContext", () => {
  it("Math.random が同一シードで決定的な値列を返す", () => {
    const first = createStabilizedContext();
    const firstVals = vm.runInContext(
      "[Math.random(), Math.random(), Math.random()]",
      first.context,
    ) as number[];

    const second = createStabilizedContext();
    const secondVals = vm.runInContext(
      "[Math.random(), Math.random(), Math.random()]",
      second.context,
    ) as number[];

    expect(firstVals).toEqual(secondVals);
    expect(new Set(firstVals).size).toBe(3);
    for (const v of firstVals) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("Date.now / new Date() / performance.now が固定値になる", () => {
    const { context } = createStabilizedContext();
    const res = vm.runInContext(
      "[Date.now(), new Date().getTime(), performance.now()]",
      context,
    ) as number[];
    expect(res).toEqual([FROZEN_EPOCH_MS, FROZEN_EPOCH_MS, FROZEN_EPOCH_MS]);
  });

  it("setTimeout / setInterval の本体は実行されない", () => {
    const { context } = createStabilizedContext();
    const res = vm.runInContext(
      `
      let touched = false;
      setTimeout(() => { touched = true; }, 0);
      setInterval(() => { touched = true; }, 0);
      touched
      `,
      context,
    ) as boolean;
    expect(res).toBe(false);
  });

  it("process / require / eval / Function は undefined として遮断されている", () => {
    const { context } = createStabilizedContext();
    const res = vm.runInContext(
      `
      [
        typeof process,
        typeof require,
        typeof eval,
        typeof Function,
      ]
      `,
      context,
    ) as string[];
    expect(res).toEqual(["undefined", "undefined", "undefined", "undefined"]);
  });

  it("console.log / error 等の呼び出しは consoleCalls に蓄積される", () => {
    const { context, consoleCalls } = createStabilizedContext();
    vm.runInContext(
      `
      console.log("a", 1);
      console.error({x: 2});
      console.warn("w");
      console.info("i");
      console.debug("d");
      `,
      context,
    );
    expect(consoleCalls).toHaveLength(5);
    expect(consoleCalls[0]).toEqual({ method: "log", args: ["a", 1] });
    expect(consoleCalls[1]?.method).toBe("error");
    expect(consoleCalls[4]?.method).toBe("debug");
  });

  it("baselineKeys で stabilizer 注入済み key が追跡できる", () => {
    const { baselineKeys } = createStabilizedContext();
    for (const k of ["console", "Math", "Date", "setTimeout", "performance", "process"]) {
      expect(baselineKeys.has(k)).toBe(true);
    }
  });
});
