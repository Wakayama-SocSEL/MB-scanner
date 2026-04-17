import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { runCheckEquivalenceBatch } from "../../src/cli/check-equivalence";

type WritableSpy = {
  writes: string[];
  original: typeof process.stdout.write;
};

function installStdoutSpy(): WritableSpy {
  const writes: string[] = [];
  const original = process.stdout.write.bind(process.stdout);
  process.stdout.write = ((chunk: unknown) => {
    writes.push(typeof chunk === "string" ? chunk : chunk instanceof Buffer ? chunk.toString("utf-8") : String(chunk));
    return true;
  }) as typeof process.stdout.write;
  return { writes, original };
}

function restoreStdout(spy: WritableSpy): void {
  process.stdout.write = spy.original;
}

function feedStdin(payload: string): () => void {
  // process.stdin を AsyncIterator 互換のモックに差し替える
  const chunks: Buffer[] = payload.length > 0 ? [Buffer.from(payload, "utf-8")] : [];
  const iterator: AsyncIterator<Buffer> = {
    next: () => {
      const next = chunks.shift();
      return Promise.resolve(next === undefined ? { value: undefined, done: true } : { value: next, done: false });
    },
  };
  const stdinProxy = process.stdin as unknown as { [Symbol.asyncIterator]: () => AsyncIterator<Buffer> };
  const originalAsyncIterator = stdinProxy[Symbol.asyncIterator];
  stdinProxy[Symbol.asyncIterator] = () => iterator;
  return () => {
    stdinProxy[Symbol.asyncIterator] = originalAsyncIterator;
  };
}

interface BatchResult {
  id?: string;
  verdict: string;
  observations: unknown[];
  error_message?: string | null;
  effective_timeout_ms?: number;
}

function parseOutput(writes: string[]): BatchResult[] {
  return writes
    .join("")
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as BatchResult);
}

function getResult(results: BatchResult[], idx: number): BatchResult {
  const r = results[idx];
  if (r === undefined) throw new Error(`expected result at index ${idx}`);
  return r;
}

describe("runCheckEquivalenceBatch", () => {
  let spy: WritableSpy;
  let restoreStdin: () => void = () => {};

  beforeEach(() => {
    spy = installStdoutSpy();
  });

  afterEach(() => {
    restoreStdout(spy);
    restoreStdin();
  });

  it("3 トリプルを順序保持で処理し id をエコーバックする", async () => {
    const payload = [
      JSON.stringify({ id: "a", slow: "1 + 1", fast: "2", timeout_ms: 5000 }),
      JSON.stringify({ id: "b", slow: "1", fast: "2", timeout_ms: 5000 }),
      JSON.stringify({ id: "c", slow: "[1,2,3]", fast: "[1,2,3]", timeout_ms: 5000 }),
    ].join("\n");
    restoreStdin = feedStdin(payload);

    const code = await runCheckEquivalenceBatch();

    expect(code).toBe(0);
    const results = parseOutput(spy.writes);
    expect(results.map((r) => r.id)).toEqual(["a", "b", "c"]);
    expect(getResult(results, 0).verdict).toBe("equal");
    expect(getResult(results, 1).verdict).toBe("not_equal");
    expect(getResult(results, 2).verdict).toBe("equal");
  });

  it("effective_timeout_ms が入力値と一致する", async () => {
    restoreStdin = feedStdin(
      JSON.stringify({ id: "x", slow: "1", fast: "1", timeout_ms: 3000 }) + "\n",
    );

    await runCheckEquivalenceBatch();

    const result = getResult(parseOutput(spy.writes), 0);
    expect(result.effective_timeout_ms).toBe(3000);
  });

  it("timeout_ms=1 で無限ループも checker に値が届く", async () => {
    restoreStdin = feedStdin(
      JSON.stringify({ id: "loop", slow: "while(true){}", fast: "while(true){}", timeout_ms: 1 }) + "\n",
    );

    await runCheckEquivalenceBatch();

    const result = getResult(parseOutput(spy.writes), 0);
    expect(result.id).toBe("loop");
    expect(result.effective_timeout_ms).toBe(1);
    // 両側 timeout → exception oracle で ctor 一致 → equal もあり得るが、
    // どちらにせよ timeout_ms=1 が checker まで届いていることがエコーバックで確認できれば十分
  });

  it("timeout_ms 欠落行は error verdict で id 付きで返す", async () => {
    restoreStdin = feedStdin(
      JSON.stringify({ id: "no_timeout", slow: "1", fast: "1" }) + "\n",
    );

    const code = await runCheckEquivalenceBatch();

    expect(code).toBe(0);
    const result = getResult(parseOutput(spy.writes), 0);
    expect(result.id).toBe("no_timeout");
    expect(result.verdict).toBe("error");
    expect(result.error_message).toContain("timeout_ms");
  });

  it("JSON parse 失敗行は他行に波及しない", async () => {
    const payload = [
      JSON.stringify({ id: "ok1", slow: "1", fast: "1", timeout_ms: 5000 }),
      "this is not json",
      JSON.stringify({ id: "ok2", slow: "2", fast: "2", timeout_ms: 5000 }),
    ].join("\n");
    restoreStdin = feedStdin(payload);

    const code = await runCheckEquivalenceBatch();

    expect(code).toBe(0);
    const results = parseOutput(spy.writes);
    expect(results).toHaveLength(3);
    expect(getResult(results, 0).id).toBe("ok1");
    expect(getResult(results, 0).verdict).toBe("equal");
    expect(getResult(results, 1).verdict).toBe("error");
    expect(getResult(results, 1).error_message).toContain("Failed to parse");
    expect(getResult(results, 2).id).toBe("ok2");
    expect(getResult(results, 2).verdict).toBe("equal");
  });

  it("空入力は空出力 + exit 0", async () => {
    restoreStdin = feedStdin("");

    const code = await runCheckEquivalenceBatch();

    expect(code).toBe(0);
    expect(spy.writes.join("")).toBe("");
  });

  it("id 欠落時は id を持たない結果を返す", async () => {
    restoreStdin = feedStdin(
      JSON.stringify({ slow: "1", fast: "1", timeout_ms: 5000 }) + "\n",
    );

    await runCheckEquivalenceBatch();

    const result = getResult(parseOutput(spy.writes), 0);
    expect(result.id).toBeUndefined();
    expect(result.verdict).toBe("equal");
  });
});
