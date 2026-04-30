import vm from "node:vm";

const FROZEN_EPOCH_MS = 0;
const PRNG_SEED = 0x42424242;

export type ConsoleMethod = "log" | "error" | "warn" | "info" | "debug";

export interface ConsoleCall {
  method: ConsoleMethod;
  args: unknown[];
}

export interface StabilizedContext {
  context: vm.Context;
  consoleCalls: ConsoleCall[];
  baselineKeys: ReadonlySet<string>;
}

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function createFrozenMath(rng: () => number): typeof Math {
  return new Proxy(Math, {
    get(target, prop, receiver) {
      if (prop === "random") return rng;
      return Reflect.get(target, prop, receiver) as unknown;
    },
  });
}

function createFrozenDate(): DateConstructor {
  return new Proxy(Date, {
    construct(target, args, newTarget) {
      const normalized = args.length === 0 ? [FROZEN_EPOCH_MS] : args;
      return Reflect.construct(target, normalized, newTarget) as Date;
    },
    get(target, prop, receiver) {
      if (prop === "now") return () => FROZEN_EPOCH_MS;
      return Reflect.get(target, prop, receiver) as unknown;
    },
  });
}

function createConsoleHook(sink: ConsoleCall[]): Record<ConsoleMethod, (...args: unknown[]) => void> {
  const methods: ConsoleMethod[] = ["log", "error", "warn", "info", "debug"];
  const hook = {} as Record<ConsoleMethod, (...args: unknown[]) => void>;
  for (const method of methods) {
    hook[method] = (...args: unknown[]) => {
      sink.push({ method, args });
    };
  }
  return hook;
}

export function createStabilizedContext(): StabilizedContext {
  const consoleCalls: ConsoleCall[] = [];
  const rng = mulberry32(PRNG_SEED);

  const sandbox: Record<string, unknown> = {
    console: createConsoleHook(consoleCalls),
    Math: createFrozenMath(rng),
    Date: createFrozenDate(),
    setTimeout: () => 0,
    setInterval: () => 0,
    setImmediate: () => 0,
    clearTimeout: () => undefined,
    clearInterval: () => undefined,
    clearImmediate: () => undefined,
    queueMicrotask: () => undefined,
    performance: { now: () => FROZEN_EPOCH_MS },
    process: undefined,
    require: undefined,
    eval: undefined,
    Function: undefined,
  };

  const context = vm.createContext(sandbox);
  const baselineKeys = new Set(Object.keys(sandbox));

  return { context, consoleCalls, baselineKeys };
}
