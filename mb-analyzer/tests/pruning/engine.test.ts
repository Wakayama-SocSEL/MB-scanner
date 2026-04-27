/**
 * 対象: src/pruning/engine.ts (Hydra 式 pruning 本体)
 * 観点:
 *   - trivially-reducible: 全候補ワイルドカード化可なケースで iterations > 0
 *   - initial_mismatch: 初回検証で slow ≢ fast なら pruning を回さない
 *   - error: parse 失敗コードで verdict=error
 *   - id エコーバック: 入力 id がそのまま結果に乗る
 */
import { describe, expect, it } from "vitest";

import { prune } from "../../src/pruning/engine";

describe("prune — trivially-reducible", () => {
  it("全候補が削除可能なケースでは pruned が返り iterations > 0", async () => {
    // slow と fast が同じなら、slow の候補はすべてワイルドカード化しても等価のまま。
    // つまり全候補が「不要」= ワイルドカード化される。
    const result = await prune({
      slow: "const x = arr[0]; use(x);",
      fast: "const x = arr[0]; use(x);",
      timeout_ms: 2000,
      max_iterations: 50,
    });
    expect(result.verdict).toBe("pruned");
    expect(result.iterations ?? 0).toBeGreaterThan(0);
    // 少なくとも 1 つ placeholder が記録される
    expect(result.placeholders?.length ?? 0).toBeGreaterThan(0);
    // node_count_after は before 以下 (prune で構造は減るか同じ)
    expect(result.node_count_after).toBeLessThanOrEqual(result.node_count_before ?? 0);
  }, 20_000);
});

describe("prune — 初回非等価の検出", () => {
  it("setup 上で slow ≢ fast なら pruning を回さず initial_mismatch", async () => {
    // ガード付き反復 (slow) と無ガード反復 (fast) を prototype chain ありの setup で
    // 評価すると結果集合が異なるので、pruning 前から非等価と判定される代表例。
    const setup = `
      function P() {}
      P.prototype.hidden = 1;
      const obj = new P();
      obj.own = 2;
    `;
    const slow = `
      const out = [];
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) { out.push(key); }
      }
      out;
    `;
    const fast = `
      const out = [];
      for (const key in obj) { out.push(key); }
      out;
    `;
    const result = await prune({
      setup,
      slow,
      fast,
      timeout_ms: 3000,
      max_iterations: 30,
    });
    expect(result.verdict).toBe("initial_mismatch");
  }, 30_000);
});

describe("prune — initial_mismatch", () => {
  it("slow と fast が最初から明確に非等価なら initial_mismatch を返す", async () => {
    const result = await prune({
      slow: "throw new Error('slow');",
      fast: "42;",
      timeout_ms: 2000,
      max_iterations: 10,
    });
    expect(result.verdict).toBe("initial_mismatch");
    // pattern 系は付与されない (plan 2.3 の仕様)
    expect(result.pattern_code).toBeUndefined();
    expect(result.placeholders?.length ?? 0).toBe(0);
  }, 20_000);
});

describe("prune — error", () => {
  it("parse 失敗コード (slow が構文エラー) なら verdict=error", async () => {
    const result = await prune({
      slow: "const x =",
      fast: "42;",
      timeout_ms: 2000,
      max_iterations: 10,
    });
    expect(result.verdict).toBe("error");
    expect(result.error_message).toBeDefined();
  });

  it("fast 側が構文エラーでも error", async () => {
    const result = await prune({
      slow: "42;",
      fast: "function",
      timeout_ms: 2000,
      max_iterations: 10,
    });
    expect(result.verdict).toBe("error");
  });
});

describe("prune — id エコーバック", () => {
  it("入力 id は結果にそのまま付与される", async () => {
    const result = await prune({
      id: "test-xyz",
      slow: "42;",
      fast: "42;",
      timeout_ms: 2000,
      max_iterations: 10,
    });
    expect(result.id).toBe("test-xyz");
  }, 20_000);
});
