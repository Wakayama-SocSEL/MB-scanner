import { describe, expect, expectTypeOf, it } from "vitest";
import {
  ALL_ORACLES,
  ORACLE,
  ORACLE_VERDICT,
  VERDICT,
  type EquivalenceCheckResult,
  type EquivalenceInput,
  type Oracle,
  type OracleObservation,
  type OracleVerdict,
  type Verdict,
} from "../../src/shared/types";

describe("VERDICT", () => {
  it("Python 側 Verdict StrEnum と同じ文字列値を持つ", () => {
    expect(VERDICT).toStrictEqual({
      EQUAL: "equal",
      NOT_EQUAL: "not_equal",
      ERROR: "error",
    });
  });

  it("Verdict 型が 3 値の union として narrow される", () => {
    expectTypeOf<Verdict>().toEqualTypeOf<"equal" | "not_equal" | "error">();
  });
});

describe("ORACLE_VERDICT", () => {
  it("Python 側 OracleVerdict StrEnum と同じ文字列値を持つ", () => {
    expect(ORACLE_VERDICT).toStrictEqual({
      EQUAL: "equal",
      NOT_EQUAL: "not_equal",
      NOT_APPLICABLE: "not_applicable",
      ERROR: "error",
    });
  });

  it("OracleVerdict 型が 4 値の union", () => {
    expectTypeOf<OracleVerdict>().toEqualTypeOf<
      "equal" | "not_equal" | "not_applicable" | "error"
    >();
  });
});

describe("ORACLE", () => {
  it("Python 側 Oracle StrEnum と同じ文字列値を持つ", () => {
    expect(ORACLE).toStrictEqual({
      RETURN_VALUE: "return_value",
      ARGUMENT_MUTATION: "argument_mutation",
      EXCEPTION: "exception",
      EXTERNAL_OBSERVATION: "external_observation",
    });
  });

  it("ALL_ORACLES が 4 値を過不足なく列挙する", () => {
    expect(ALL_ORACLES).toHaveLength(4);
    expect(new Set(ALL_ORACLES)).toEqual(new Set(Object.values(ORACLE)));
  });
});

describe("EquivalenceInput", () => {
  it("slow / fast 必須、setup / timeout_ms は任意", () => {
    const minimal: EquivalenceInput = { slow: "1", fast: "1" };
    const full: EquivalenceInput = {
      setup: "const x = 1;",
      slow: "x",
      fast: "x",
      timeout_ms: 5000,
    };
    expect(minimal.slow).toBe("1");
    expect(full.timeout_ms).toBe(5000);
  });
});

describe("OracleObservation", () => {
  it("JSON 往復でフィールド名と値が保持される", () => {
    const obs: OracleObservation = {
      oracle: ORACLE.RETURN_VALUE,
      verdict: ORACLE_VERDICT.NOT_EQUAL,
      slow_value: "-1",
      fast_value: "1",
      detail: null,
    };
    const parsed = JSON.parse(JSON.stringify(obs)) as OracleObservation;
    expect(parsed).toStrictEqual(obs);
    expect(Object.keys(parsed)).toEqual([
      "oracle",
      "verdict",
      "slow_value",
      "fast_value",
      "detail",
    ]);
  });
});

describe("EquivalenceCheckResult", () => {
  it("equal verdict は observations を含む", () => {
    const result: EquivalenceCheckResult = {
      verdict: VERDICT.EQUAL,
      observations: [
        { oracle: ORACLE.RETURN_VALUE, verdict: ORACLE_VERDICT.EQUAL },
        { oracle: ORACLE.ARGUMENT_MUTATION, verdict: ORACLE_VERDICT.NOT_APPLICABLE },
        { oracle: ORACLE.EXCEPTION, verdict: ORACLE_VERDICT.NOT_APPLICABLE },
        { oracle: ORACLE.EXTERNAL_OBSERVATION, verdict: ORACLE_VERDICT.NOT_APPLICABLE },
      ],
    };
    expect(result.observations).toHaveLength(4);
  });

  it("error verdict は error_message を伴える", () => {
    const result: EquivalenceCheckResult = {
      verdict: VERDICT.ERROR,
      observations: [],
      error_message: "timeout",
    };
    expect(result.error_message).toBe("timeout");
  });

  it("Oracle 型は readonly union として narrow される", () => {
    expectTypeOf<Oracle>().toEqualTypeOf<
      "return_value" | "argument_mutation" | "exception" | "external_observation"
    >();
  });
});
