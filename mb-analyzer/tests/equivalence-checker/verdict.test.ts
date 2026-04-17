import { describe, expect, it } from "vitest";
import { deriveOverallVerdict } from "../../src/equivalence-checker/verdict";
import { ORACLE, ORACLE_VERDICT, type OracleObservation } from "../../src/shared/types";

function obs(verdict: OracleObservation["verdict"]): OracleObservation {
  return { oracle: ORACLE.RETURN_VALUE, verdict };
}

describe("deriveOverallVerdict", () => {
  it("not_equal が 1 つでもあれば not_equal（最優先）", () => {
    expect(
      deriveOverallVerdict([obs(ORACLE_VERDICT.NOT_EQUAL), obs(ORACLE_VERDICT.EQUAL)]),
    ).toBe("not_equal");
  });

  it("not_equal がなく error があれば error", () => {
    expect(
      deriveOverallVerdict([obs(ORACLE_VERDICT.EQUAL), obs(ORACLE_VERDICT.ERROR)]),
    ).toBe("error");
  });

  it("全 not_applicable なら error", () => {
    expect(
      deriveOverallVerdict([
        obs(ORACLE_VERDICT.NOT_APPLICABLE),
        obs(ORACLE_VERDICT.NOT_APPLICABLE),
        obs(ORACLE_VERDICT.NOT_APPLICABLE),
        obs(ORACLE_VERDICT.NOT_APPLICABLE),
      ]),
    ).toBe("error");
  });

  it("equal が 1 つでもあり、error/not_equal なしなら equal", () => {
    expect(
      deriveOverallVerdict([
        obs(ORACLE_VERDICT.EQUAL),
        obs(ORACLE_VERDICT.NOT_APPLICABLE),
      ]),
    ).toBe("equal");
  });

  it("空 observation は error", () => {
    expect(deriveOverallVerdict([])).toBe("error");
  });
});
