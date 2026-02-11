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

## 2. 新しい比較ストラテジーの追加

### 目的
等価性を判定する新しい方法を追加します（例: メモリ使用量、実行時間など）。

### 手順

#### 2-1. ストラテジーファイルの作成
`mb_scanner/resources/benchmark/strategies/` に新しいJavaScriptファイルを作成します。

**ファイル構造**:
```javascript
const { createSandbox } = require('../sandbox.js');

function compareByNewStrategy(slowCode, fastCode) {
  const sandbox = createSandbox(console.log);

  // slowCode と fastCode を実行して比較
  // ...

  // 結果を出力: "equal", "not_equal", "error" のいずれか
  console.log("equal");
}

// コマンドライン引数からコードを受け取る
const slowCode = process.argv[2];
const fastCode = process.argv[3];
compareByNewStrategy(slowCode, fastCode);
```

**重要事項**:
- `sandbox.js` を必ずインポートし、サンドボックス環境を使用すること
- 標準出力に結果（`equal`, `not_equal`, `error`）を出力すること

#### 2-2. Pythonサービスの更新
`mb_scanner/services/benchmark_runner.py` で新しいストラテジーを認識できるように更新します。

```python
STRATEGIES = ["stdout", "functions", "variables", "new_strategy"]

def run_equivalence_check(
    benchmark_dir: Path,
    strategy: str = "stdout",
    timeout: int = 10,
) -> EquivalenceCheckResult:
    # 新しいストラテジーの実行ロジックを追加
    ...
```

#### 2-3. テストの追加
新しいストラテジーの動作を検証するテストを `tests/services/test_benchmark_runner.py` に追加します。

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
