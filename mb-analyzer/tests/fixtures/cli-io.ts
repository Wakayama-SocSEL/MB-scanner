/**
 * CLI E2E テスト用の stdin/stdout/stderr spy ヘルパ。
 * process.stdout/stderr.write をキャプチャし、process.stdin を AsyncIterator モックに
 * 差し替えることで、subprocess を起こさずに CLI 契約 (JSON I/O + exit code) を検証する。
 *
 * lifecycle を持つため `test.extend` 化もできるが、既存テストの beforeEach/afterEach 構造を
 * 維持したいので現状は直接 import で使う pure factory として提供。
 */

export type WritableSpy = {
  writes: string[];
  original: typeof process.stdout.write;
};

export function installSpy(target: "stdout" | "stderr"): WritableSpy {
  const stream = process[target];
  const writes: string[] = [];
  const original = stream.write.bind(stream);
  stream.write = ((chunk: unknown) => {
    writes.push(
      typeof chunk === "string"
        ? chunk
        : chunk instanceof Buffer
          ? chunk.toString("utf-8")
          : String(chunk),
    );
    return true;
  }) as typeof stream.write;
  return { writes, original };
}

export function restoreSpy(target: "stdout" | "stderr", spy: WritableSpy): void {
  process[target].write = spy.original;
}

export function feedStdin(payload: string): () => void {
  const chunks: Buffer[] = payload.length > 0 ? [Buffer.from(payload, "utf-8")] : [];
  const iterator: AsyncIterator<Buffer> = {
    next: () => {
      const next = chunks.shift();
      return Promise.resolve(
        next === undefined ? { value: undefined, done: true } : { value: next, done: false },
      );
    },
  };
  const stdinProxy = process.stdin as unknown as {
    [Symbol.asyncIterator]: () => AsyncIterator<Buffer>;
  };
  const originalAsyncIterator = stdinProxy[Symbol.asyncIterator];
  stdinProxy[Symbol.asyncIterator] = () => iterator;
  return () => {
    stdinProxy[Symbol.asyncIterator] = originalAsyncIterator;
  };
}
