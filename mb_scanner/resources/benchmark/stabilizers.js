/**
 * stabilizers.js
 *
 * 非決定的な関数を固定値を返すように安定化するモジュール。
 * 実行環境の設定が肥大化した場合でも、このモジュールに集約される。
 */

/**
 * シード付き疑似乱数生成器（線形合同法: LCG）
 *
 * 同じシード値を使用すると、常に同じ乱数シーケンスを生成する。
 * これにより、Math.random() の呼び出しが決定的になる。
 *
 * @param {number} seed - 初期シード値
 * @returns {function(): number} 0.0～1.0の疑似乱数を返す関数
 */
function seededRandom(seed) {
  let state = seed;
  return function () {
    // 線形合同法の係数（glibc の実装を参考）
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

// デフォルト設定
const FIXED_TIMESTAMP = 1609459200000; // 2021-01-01 00:00:00 UTC
const DEFAULT_SEED = 12345;

/**
 * 安定化されたMathオブジェクトを作成する
 *
 * Math.random() が決定的な乱数シーケンスを返すようにする。
 *
 * @param {number} [seed=DEFAULT_SEED] - 疑似乱数生成器のシード値
 * @returns {object} 安定化されたMathオブジェクト
 */
function createStabilizedMath(seed = DEFAULT_SEED) {
  const stabilizedMath = Object.create(Math);
  stabilizedMath.random = seededRandom(seed);
  return stabilizedMath;
}

/**
 * 安定化されたDateコンストラクタを作成する
 *
 * new Date() と Date.now() が固定のタイムスタンプを返すようにする。
 *
 * @param {number} [timestamp=FIXED_TIMESTAMP] - 固定タイムスタンプ（ミリ秒）
 * @returns {function} 安定化されたDateコンストラクタ
 */
function createStabilizedDate(timestamp = FIXED_TIMESTAMP) {
  const OriginalDate = Date;

  function StabilizedDate(...args) {
    if (args.length === 0) {
      // 引数なしの場合は固定タイムスタンプを使用
      return new OriginalDate(timestamp);
    }
    // 引数ありの場合は通常通り
    return new OriginalDate(...args);
  }

  // 静的メソッドのコピー
  StabilizedDate.now = () => timestamp;
  StabilizedDate.parse = OriginalDate.parse;
  StabilizedDate.UTC = OriginalDate.UTC;
  StabilizedDate.prototype = OriginalDate.prototype;

  return StabilizedDate;
}

module.exports = {
  createStabilizedMath,
  createStabilizedDate,
};
