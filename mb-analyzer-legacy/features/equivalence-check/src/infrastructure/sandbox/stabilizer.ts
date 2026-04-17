/**
 * stabilizer.ts
 *
 * 非決定的な関数を固定値を返すように安定化するモジュール。
 */

const FIXED_TIMESTAMP = 1609459200000; // 2021-01-01 00:00:00 UTC
const DEFAULT_SEED = 12345;

function seededRandom(seed: number): () => number {
  let state = seed;
  return function () {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

export function createStabilizedMath(seed: number = DEFAULT_SEED): Math {
  const stabilizedMath = Object.create(Math) as Math;
  (stabilizedMath as { random: () => number }).random = seededRandom(seed);
  return stabilizedMath;
}

type DateConstructor = {
  new (): Date;
  new (value: number | string | Date): Date;
  now(): number;
  parse(s: string): number;
  UTC(year: number, month: number, ...rest: number[]): number;
  prototype: Date;
};

export function createStabilizedDate(timestamp: number = FIXED_TIMESTAMP): DateConstructor {
  const OriginalDate = Date;

  function StabilizedDate(...args: [] | ConstructorParameters<typeof Date>): Date {
    if (args.length === 0) {
      return new OriginalDate(timestamp);
    }
    return new OriginalDate(...(args as ConstructorParameters<typeof Date>));
  }

  StabilizedDate.now = (): number => timestamp;
  StabilizedDate.parse = OriginalDate.parse;
  StabilizedDate.UTC = OriginalDate.UTC;
  StabilizedDate.prototype = OriginalDate.prototype;

  return StabilizedDate as unknown as DateConstructor;
}
