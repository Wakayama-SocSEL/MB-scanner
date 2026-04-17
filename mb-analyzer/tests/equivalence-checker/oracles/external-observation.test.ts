import { describe, expect, it } from "vitest";
import { checkExternalObservation } from "../../../src/equivalence-checker/oracles/external-observation";
import type { ExecutionCapture } from "../../../src/equivalence-checker/sandbox/executor";
import type { ConsoleCall } from "../../../src/equivalence-checker/sandbox/stabilizer";

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

const logA: ConsoleCall = { method: "log", args: ["a", 1] };
const logB: ConsoleCall = { method: "log", args: ["b"] };

describe("checkExternalObservation", () => {
  it("console 空 & new_globals 空 → not_applicable", () => {
    expect(checkExternalObservation(capture(), capture()).verdict).toBe("not_applicable");
  });

  it("console 列が完全一致 & globals 一致 → equal", () => {
    const s = capture({ console_log: [logA], new_globals: ["g"] });
    const f = capture({ console_log: [logA], new_globals: ["g"] });
    expect(checkExternalObservation(s, f).verdict).toBe("equal");
  });

  it("console 列が異なる → not_equal", () => {
    const s = capture({ console_log: [logA] });
    const f = capture({ console_log: [logB] });
    const obs = checkExternalObservation(s, f);
    expect(obs.verdict).toBe("not_equal");
    expect(obs.detail).toContain("console");
  });

  it("new_globals 集合が違う → not_equal", () => {
    const s = capture({ new_globals: ["a"] });
    const f = capture({ new_globals: ["b"] });
    const obs = checkExternalObservation(s, f);
    expect(obs.verdict).toBe("not_equal");
    expect(obs.detail).toContain("new_globals");
  });

  it("console の順序が違うと not_equal", () => {
    const s = capture({ console_log: [logA, logB] });
    const f = capture({ console_log: [logB, logA] });
    expect(checkExternalObservation(s, f).verdict).toBe("not_equal");
  });

  it("循環参照を含む args → error", () => {
    const cyc: Record<string, unknown> = {};
    cyc.self = cyc;
    const s = capture({ console_log: [{ method: "log", args: [cyc] }] });
    const f = capture({ console_log: [{ method: "log", args: ["x"] }] });
    expect(checkExternalObservation(s, f).verdict).toBe("error");
  });
});
