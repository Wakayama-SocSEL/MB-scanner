# ベンチマーク機能拡張ガイド

ベンチマークの等価性チェック機能に関する拡張方法を説明します。

## 概要
ベンチマーク機能は、JavaScriptコードの等価性を検証するために、Node.jsサンドボックス環境でコードを実行し、複数の比較ストラテジーで結果を比較します。

### 主要コンポーネント
- **サンドボックス環境** (`sandbox.js`): 分離された実行環境を提供
- **安定化処理** (`stabilizers.js`): 非決定的な関数の固定化
- **比較ストラテジー** (`strategies/`): 等価性を判定するルール

## 1. サンドボックス環境のカスタマイズ

### 目的
実行環境の設定を変更し、テスト実行時の一貫性を保証します。

### 手順

#### 1-1. 安定化処理の追加
`mb_scanner/resources/benchmark/stabilizers.js` に新しい固定化ロジックを追加します。

**実装例**（非決定的な関数の固定化）:
```javascript
// Math.random() をシード付き疑似乱数生成器に置き換え
function seededRandom(seed) {
  let state = seed;
  return function() {
    state = (state * 1103515245 + 12345) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

// Date.now() を固定タイムスタンプに置き換え
const FIXED_TIMESTAMP = 1609459200000; // 2021-01-01 00:00:00 UTC
```

**設計原則**:
- **モジュール分離**: サンドボックス設定の肥大化を防ぐため、安定化ロジックは `stabilizers.js` に分離
- **決定性**: 実行のたびに同じ結果が得られるよう、シード値や固定値を使用

#### 1-2. サンドボックスへの統合
`mb_scanner/resources/benchmark/sandbox.js` の `createSandbox` 関数で安定化処理を適用します。

```javascript
const { createStabilizedMath, createStabilizedDate } = require('./stabilizers.js');

function createSandbox(logFn) {
  return {
    Math: createStabilizedMath(),
    Date: createStabilizedDate(),
    // ... その他のグローバルオブジェクト
  };
}
```

#### 1-3. テストの追加
`tests/services/test_benchmark_runner.py` に、新しい安定化処理が正しく動作することを確認するテストを追加します。

```python
def test_equivalence_check_with_nondeterministic_functions(tmp_path: Path) -> None:
    """非決定的な関数を含むコードの等価性チェック"""
    # テストコードを作成し、等価性が正しく判定されることを確認
    ...
```

## 2. 比較ストラテジーのアーキテクチャ

### 現在の実装（2026年2月）
- **全戦略実行**: 適用可能な全ての戦略を実行し、結果を `strategy_results` 配列に格納
- **stdout戦略の特別扱い**: 適用可能なら他の戦略を実行せず即返し
- **ステータス判定**: 全て"equal"なら"equal"、1つでも"not_equal"なら"not_equal"

### データフロー
1. **Node.js側** (`runner.js`): 各戦略を実行し、結果をJSON出力
2. **Python側** (`benchmark_runner.py`): JSONをパースして `EquivalenceResult` に変換
3. **モデル定義** (`models/benchmark.py`):
   - `StrategyResult`: 個別戦略の結果
   - `EquivalenceResult`: 全戦略の結果を含む総合結果

### 新しい戦略の追加手順
1. `strategies/` に新ストラテジークラスを作成（`canApply()`, `compare()` 実装）
2. `runner.js` で戦略リストに追加
3. `models/benchmark.py` の `comparison_method` Literal に追加
4. テスト追加 (`tests/services/test_benchmark_runner.py`)

## 3. 設計上の注意点

### モジュール分離の重要性
- サンドボックス環境の設定が肥大化する可能性を考慮し、機能ごとにモジュールを分離
- 各モジュールは単一責任の原則に従い、明確な役割を持つ

### 決定性の保証
- ベンチマークの等価性チェックでは、実行のたびに同じ結果が得られることが重要
- 非決定的な関数（`Math.random()`, `Date.now()`, `process.hrtime()` など）は必ず固定化すること

### テストの充実
- 新しい機能を追加する際は、必ずテストを作成すること
- エッジケース（エラー処理、タイムアウト、メモリ不足など）も考慮すること
