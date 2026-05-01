import { prune } from "../pruning";
import type { PruningInput, PruningResult } from "../shared/pruning-contracts";

const EXIT_PRUNED = 0;
const EXIT_INITIAL_MISMATCH = 1;
const EXIT_ERROR = 2;
const EXIT_BATCH_OK = 0;
const EXIT_BATCH_IO_FAILURE = 2;

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk as string));
  }
  return Buffer.concat(chunks).toString("utf-8");
}

function parseInput(raw: string): PruningInput | string {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return `Failed to parse stdin as JSON: ${e instanceof Error ? e.message : "unknown"}`;
  }
  if (parsed === null || typeof parsed !== "object") {
    return "Expected a JSON object on stdin";
  }
  const obj = parsed as Record<string, unknown>;
  if (typeof obj.slow !== "string") return "'slow' field must be a string";
  if (typeof obj.fast !== "string") return "'fast' field must be a string";

  const input: PruningInput = { slow: obj.slow, fast: obj.fast };
  if (obj.setup !== undefined) {
    if (typeof obj.setup !== "string") return "'setup' field must be a string when present";
    input.setup = obj.setup;
  }
  if (obj.timeout_ms !== undefined) {
    if (typeof obj.timeout_ms !== "number" || !Number.isFinite(obj.timeout_ms)) {
      return "'timeout_ms' field must be a finite number when present";
    }
    input.timeout_ms = obj.timeout_ms;
  }
  if (obj.max_iterations !== undefined) {
    if (typeof obj.max_iterations !== "number" || !Number.isFinite(obj.max_iterations)) {
      return "'max_iterations' field must be a finite number when present";
    }
    input.max_iterations = obj.max_iterations;
  }
  return input;
}

export async function runPrune(): Promise<number> {
  const raw = await readStdin();
  const parsed = parseInput(raw);
  if (typeof parsed === "string") {
    process.stderr.write(`${parsed}\n`);
    return EXIT_ERROR;
  }

  const result = await prune(parsed);
  process.stdout.write(`${JSON.stringify(result)}\n`);

  if (result.verdict === "pruned") return EXIT_PRUNED;
  if (result.verdict === "initial_mismatch") return EXIT_INITIAL_MISMATCH;
  return EXIT_ERROR;
}

// バッチ API は単発と異なり `timeout_ms` を **必須** とする。
// Python→Node への受け渡しで timeout_ms が落ちて DEFAULT にサイレントフォールバック
// する事故を防ぐため (equivalence 側と同じ判断、本 PR でも踏襲)。
// `max_iterations` は optional のまま (engine が default を解決)。
function parseBatchLine(raw: string): PruningInput | { id: string | undefined; error: string } {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return {
      id: undefined,
      error: `Failed to parse line as JSON: ${e instanceof Error ? e.message : "unknown"}`,
    };
  }
  if (parsed === null || typeof parsed !== "object") {
    return { id: undefined, error: "Expected a JSON object per line" };
  }
  const obj = parsed as Record<string, unknown>;
  const id = typeof obj.id === "string" ? obj.id : undefined;

  if (typeof obj.slow !== "string") return { id, error: "'slow' field must be a string" };
  if (typeof obj.fast !== "string") return { id, error: "'fast' field must be a string" };
  if (obj.timeout_ms === undefined) {
    return { id, error: "'timeout_ms' field is required in batch mode" };
  }
  if (typeof obj.timeout_ms !== "number" || !Number.isFinite(obj.timeout_ms)) {
    return { id, error: "'timeout_ms' field must be a finite number" };
  }

  const input: PruningInput = {
    slow: obj.slow,
    fast: obj.fast,
    timeout_ms: obj.timeout_ms,
  };
  if (id !== undefined) input.id = id;
  if (obj.setup !== undefined) {
    if (typeof obj.setup !== "string") return { id, error: "'setup' field must be a string when present" };
    input.setup = obj.setup;
  }
  if (obj.max_iterations !== undefined) {
    if (typeof obj.max_iterations !== "number" || !Number.isFinite(obj.max_iterations)) {
      return { id, error: "'max_iterations' field must be a finite number when present" };
    }
    input.max_iterations = obj.max_iterations;
  }
  return input;
}

function errorResult(id: string | undefined, message: string): PruningResult {
  const result: PruningResult = {
    verdict: "error",
    error_message: message,
  };
  if (id !== undefined) result.id = id;
  return result;
}

export async function runPruneBatch(): Promise<number> {
  let raw: string;
  try {
    raw = await readStdin();
  } catch (e) {
    process.stderr.write(`Failed to read stdin: ${e instanceof Error ? e.message : "unknown"}\n`);
    return EXIT_BATCH_IO_FAILURE;
  }

  const lines = raw.split("\n").filter((line) => line.length > 0);
  for (const line of lines) {
    const parsed = parseBatchLine(line);
    let result: PruningResult;
    if ("error" in parsed) {
      result = errorResult(parsed.id, parsed.error);
    } else {
      const input = parsed;
      const pruneResult = await prune(input);
      result = { ...pruneResult };
      if (input.id !== undefined) result.id = input.id;
    }
    process.stdout.write(`${JSON.stringify(result)}\n`);
  }

  return EXIT_BATCH_OK;
}
