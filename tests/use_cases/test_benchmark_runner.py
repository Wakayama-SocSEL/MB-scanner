"""ベンチマーク等価性チェックサービスのテスト"""

from pathlib import Path

import pytest

from mb_scanner.use_cases.benchmark_runner import (
    run_batch_equivalence_check,
    run_equivalence_check,
)

RUNNER_JS_PATH = (
    Path(__file__).parent.parent.parent
    / "mb-analyzer"
    / "apps"
    / "equivalence-runner"
    / "dist"
    / "index.js"
)


@pytest.fixture()
def benchmark_dir(tmp_path: Path) -> Path:
    """テスト用のベンチマークディレクトリを作成する"""
    return tmp_path


def _create_entry(base_dir: Path, entry_id: int, slow_code: str, fast_code: str) -> Path:
    """テスト用のid_*ディレクトリとslow.js/fast.jsを作成する"""
    entry_dir = base_dir / f"id_{entry_id}"
    entry_dir.mkdir(parents=True, exist_ok=True)
    (entry_dir / "slow.js").write_text(slow_code, encoding="utf-8")
    (entry_dir / "fast.js").write_text(fast_code, encoding="utf-8")
    return entry_dir


class TestRunEquivalenceCheck:
    """run_equivalence_check のテスト"""

    def test_equal_stdout(self, benchmark_dir: Path) -> None:
        """console.logの出力が一致する場合、equalを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            0,
            'console.log("hello");',
            'console.log("hello");',
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"
        # equal な結果は stderr にのみ出力されるため strategy_results は空
        assert result.strategy_results == []

    def test_not_equal_stdout(self, benchmark_dir: Path) -> None:
        """console.logの出力が不一致の場合、not_equalを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            1,
            'console.log("hello");',
            'console.log("world");',
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "not_equal"
        assert len(result.strategy_results) == 1
        assert result.strategy_results[0].comparison_method == "stdout"
        assert result.strategy_results[0].status == "not_equal"

    def test_equal_variables(self, benchmark_dir: Path) -> None:
        """VAR_変数の最終状態が一致する場合、equalを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            2,
            "var VAR_1 = 10; var VAR_2 = 20;",
            "var VAR_1 = 5 + 5; var VAR_2 = 10 * 2;",
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"
        assert result.strategy_results == []

    def test_not_equal_variables(self, benchmark_dir: Path) -> None:
        """VAR_変数の最終状態が不一致の場合、not_equalを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            3,
            "var VAR_1 = 10;",
            "var VAR_1 = 99;",
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "not_equal"
        assert len(result.strategy_results) == 1
        assert result.strategy_results[0].comparison_method == "variables"

    def test_equal_functions(self, benchmark_dir: Path) -> None:
        """FUNCTION_*の戻り値が一致する場合、equalを返す"""
        slow_code = (
            "var VAR_1 = [3, 1, 2];\nfunction FUNCTION_1(arr) { return arr.slice().sort(); }\nFUNCTION_1(VAR_1);\n"
        )
        fast_code = (
            "var VAR_1 = [3, 1, 2];\n"
            "function FUNCTION_1(arr) { var sorted = arr.slice(); sorted.sort(); return sorted; }\n"
            "FUNCTION_1(VAR_1);\n"
        )
        entry_dir = _create_entry(benchmark_dir, 7, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"
        assert result.strategy_results == []

    def test_not_equal_functions(self, benchmark_dir: Path) -> None:
        """FUNCTION_*の戻り値が不一致の場合、not_equalを返す"""
        slow_code = "function FUNCTION_1(x) { return x * 2; }\nFUNCTION_1(5);\n"
        fast_code = "function FUNCTION_1(x) { return x * 3; }\nFUNCTION_1(5);\n"
        entry_dir = _create_entry(benchmark_dir, 8, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "not_equal"
        assert len(result.strategy_results) == 1
        assert result.strategy_results[0].comparison_method == "functions"

    def test_skipped_no_output_no_vars(self, benchmark_dir: Path) -> None:
        """console.logもVAR_変数もない場合、skippedを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            4,
            "function id_0(x) { return x; }",
            "function id_0(x) { return x; }",
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "skipped"

    def test_error_runtime(self, benchmark_dir: Path) -> None:
        """実行時エラーが発生する場合、errorを返す"""
        entry_dir = _create_entry(
            benchmark_dir,
            5,
            "var VAR_1 = undefinedVar.prop;",
            "var VAR_1 = 1;",
        )
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "error"
        # エラーは strategy_results の中に含まれる
        assert len(result.strategy_results) > 0
        assert result.strategy_results[0].error_message is not None

    def test_missing_files(self, benchmark_dir: Path) -> None:
        """slow.jsまたはfast.jsが存在しない場合、errorを返す"""
        entry_dir = benchmark_dir / "id_6"
        entry_dir.mkdir(parents=True, exist_ok=True)
        # ファイルを作成しない

        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "error"
        assert result.error_message is not None

    def test_equal_with_math_random_stdout(self, benchmark_dir: Path) -> None:
        """Math.random()を使用するコードでも、シード固定により等価判定できる（stdout戦略）"""
        slow_code = """
var arr = [];
for (var i = 0; i < 10; i++) {
    arr.push(Math.random());
}
console.log(JSON.stringify(arr));
"""
        fast_code = """
var arr = [];
for (var i = 0; i < 10; i++) {
    arr.push(Math.random());
}
console.log(JSON.stringify(arr));
"""
        entry_dir = _create_entry(benchmark_dir, 100, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"

    def test_equal_with_math_random_variables(self, benchmark_dir: Path) -> None:
        """Math.random()を使用するコードでも、シード固定により等価判定できる（variables戦略）"""
        slow_code = """
var VAR_1 = [];
for (var i = 0; i < 5; i++) {
    VAR_1.push(Math.floor(100 * Math.random()));
}
"""
        fast_code = """
var VAR_1 = [];
for (var i = 0; i < 5; i++) {
    VAR_1.push(Math.floor(100 * Math.random()));
}
"""
        entry_dir = _create_entry(benchmark_dir, 101, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"

    def test_equal_with_date_now(self, benchmark_dir: Path) -> None:
        """Date.now()を使用するコードでも、タイムスタンプ固定により等価判定できる"""
        slow_code = """
var VAR_1 = Date.now();
console.log(VAR_1);
"""
        fast_code = """
var VAR_1 = Date.now();
console.log(VAR_1);
"""
        entry_dir = _create_entry(benchmark_dir, 102, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"

    def test_equal_with_new_date(self, benchmark_dir: Path) -> None:
        """New Date()を使用するコードでも、タイムスタンプ固定により等価判定できる"""
        slow_code = """
var VAR_1 = new Date();
console.log(VAR_1.getTime());
"""
        fast_code = """
var VAR_1 = new Date();
console.log(VAR_1.getTime());
"""
        entry_dir = _create_entry(benchmark_dir, 103, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        assert result.status == "equal"

    def test_equal_with_math_random_sorting(self, benchmark_dir: Path) -> None:
        """Math.random()で生成した配列のソート結果を比較（id_0のようなケース）

        functions戦略は equal（戻り値が一致）だが、
        variables戦略は not_equal（VAR_1がfast版で変更されるため）。
        equal な戦略結果は stderr にのみ出力され、strategy_results には含まれない。
        """
        slow_code = """
var VAR_1 = Array.apply(null, Array(100)).map(function () {
  return Math.floor(1000 * Math.random());
});
function FUNCTION_1(arr) {
  return arr.filter(function (x, i, a) {
    return a.indexOf(x) === i;
  }).sort(function (a, b) {
    return a - b;
  });
}
FUNCTION_1(VAR_1);
"""
        # fast版もslow版と同じ数値ソートを使用（文字列ソートだと結果が異なる）
        fast_code = """
var VAR_1 = Array.apply(null, Array(100)).map(function () {
  return Math.floor(1000 * Math.random());
});
function FUNCTION_1(arr) {
  return arr.sort(function (a, b) {
    return a - b;
  }).filter(function (x, i) {
    return x !== arr[i + 1];
  });
}
FUNCTION_1(VAR_1);
"""
        entry_dir = _create_entry(benchmark_dir, 104, slow_code, fast_code)
        result = run_equivalence_check(entry_dir, runner_js_path=RUNNER_JS_PATH)

        # functions戦略（equal）は stderr のみ → strategy_results に含まれない
        # variables戦略（not_equal）のみ strategy_results に含まれる
        assert result.status == "not_equal"
        assert len(result.strategy_results) == 1
        assert result.strategy_results[0].comparison_method == "variables"
        assert result.strategy_results[0].status == "not_equal"


class TestRunBatchEquivalenceCheck:
    """run_batch_equivalence_check のテスト"""

    def test_batch_basic(self, benchmark_dir: Path) -> None:
        """複数エントリをバッチで処理できる"""
        _create_entry(benchmark_dir, 0, 'console.log("a");', 'console.log("a");')
        _create_entry(benchmark_dir, 1, "var VAR_1 = 1;", "var VAR_1 = 1;")
        _create_entry(benchmark_dir, 2, 'console.log("x");', 'console.log("y");')

        summary = run_batch_equivalence_check(benchmark_dir, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 3
        assert summary.equal == 2
        assert summary.not_equal == 1
        assert len(summary.results) == 3

    def test_batch_with_id_filter(self, benchmark_dir: Path) -> None:
        """IDフィルタで対象を限定できる"""
        _create_entry(benchmark_dir, 0, 'console.log("a");', 'console.log("a");')
        _create_entry(benchmark_dir, 1, 'console.log("b");', 'console.log("b");')
        _create_entry(benchmark_dir, 2, 'console.log("c");', 'console.log("c");')

        summary = run_batch_equivalence_check(benchmark_dir, target_ids={0, 2}, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 2
        assert all(r.id in {0, 2} for r in summary.results)

    def test_batch_with_count(self, benchmark_dir: Path) -> None:
        """Count で件数を制限できる"""
        _create_entry(benchmark_dir, 0, 'console.log("a");', 'console.log("a");')
        _create_entry(benchmark_dir, 1, 'console.log("b");', 'console.log("b");')
        _create_entry(benchmark_dir, 2, 'console.log("c");', 'console.log("c");')

        summary = run_batch_equivalence_check(benchmark_dir, count=2, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 2

    def test_batch_with_offset(self, benchmark_dir: Path) -> None:
        """Offset で開始位置をスキップできる"""
        _create_entry(benchmark_dir, 0, 'console.log("a");', 'console.log("a");')
        _create_entry(benchmark_dir, 1, 'console.log("b");', 'console.log("b");')
        _create_entry(benchmark_dir, 2, 'console.log("c");', 'console.log("c");')

        summary = run_batch_equivalence_check(benchmark_dir, offset=1, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 2
        assert summary.results[0].id == 1

    def test_batch_empty_dir(self, benchmark_dir: Path) -> None:
        """id_*ディレクトリがない場合、空の結果を返す"""
        summary = run_batch_equivalence_check(benchmark_dir, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 0
        assert summary.results == []

    def test_batch_parallel_execution(self, benchmark_dir: Path) -> None:
        """並列実行でも結果がIDでソートされる"""
        for i in range(10):
            _create_entry(benchmark_dir, i, f'console.log("{i}");', f'console.log("{i}");')

        summary = run_batch_equivalence_check(benchmark_dir, workers=4, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 10
        assert summary.equal == 10
        assert [r.id for r in summary.results] == list(range(10))

    def test_batch_workers_1(self, benchmark_dir: Path) -> None:
        """workers=1で逐次実行と同じ結果になる"""
        _create_entry(benchmark_dir, 0, 'console.log("a");', 'console.log("a");')
        _create_entry(benchmark_dir, 1, 'console.log("x");', 'console.log("y");')

        summary = run_batch_equivalence_check(benchmark_dir, workers=1, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 2
        assert summary.equal == 1
        assert summary.not_equal == 1

    def test_batch_workers_minus_1(self, benchmark_dir: Path) -> None:
        """workers=-1で全CPUコアを使用する"""
        for i in range(5):
            _create_entry(benchmark_dir, i, f'console.log("{i}");', f'console.log("{i}");')

        summary = run_batch_equivalence_check(benchmark_dir, workers=-1, runner_js_path=RUNNER_JS_PATH)

        assert summary.total == 5
        assert summary.equal == 5
        assert [r.id for r in summary.results] == list(range(5))
