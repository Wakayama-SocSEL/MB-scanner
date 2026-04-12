"""ベンチマークCLIコマンドのテスト"""

import json
from pathlib import Path

from typer.testing import CliRunner

from mb_scanner.adapters.cli.benchmark import benchmark_app

runner = CliRunner()


class TestBenchmarkExtractCommand:
    """mb-scanner benchmark extractコマンドのテスト"""

    def _create_jsonl_file(self, path: Path, entries: list[dict[str, object]]) -> None:
        """テスト用のJSONLファイルを作成する"""
        with path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def test_extract_single_entry(self, tmp_path: Path) -> None:
        """単一エントリの抽出が正しく動作することを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {
                    "id": 0,
                    "slow": "var x = 1;",
                    "fast": "let x = 1;",
                    "slow-fast_mediTime": 100.5,
                },
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file)])

        # Assert
        assert result.exit_code == 0
        assert "Created: 1" in result.stdout

        # ファイルが正しく作成されたことを確認
        entry_dir = tmp_path / "id_0"
        assert entry_dir.exists()
        assert (entry_dir / "slow.js").read_text() == "var x = 1;"
        assert (entry_dir / "fast.js").read_text() == "let x = 1;"

    def test_extract_multiple_entries(self, tmp_path: Path) -> None:
        """複数エントリの抽出が正しく動作することを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file)])

        # Assert
        assert result.exit_code == 0
        assert "Created: 3" in result.stdout

        for i in range(3):
            entry_dir = tmp_path / f"id_{i}"
            assert entry_dir.exists()
            assert (entry_dir / "slow.js").read_text() == f"code{i}_slow"
            assert (entry_dir / "fast.js").read_text() == f"code{i}_fast"

    def test_extract_with_id_filter(self, tmp_path: Path) -> None:
        """--idオプションで特定IDのみ抽出できることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--id", "1"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 1" in result.stdout

        # id_1のみ作成されていることを確認
        assert not (tmp_path / "id_0").exists()
        assert (tmp_path / "id_1").exists()
        assert not (tmp_path / "id_2").exists()

    def test_extract_with_ids_filter(self, tmp_path: Path) -> None:
        """--idsオプションで複数IDを抽出できることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
                {"id": 3, "slow": "code3_slow", "fast": "code3_fast", "slow-fast_mediTime": 400.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--ids", "0,2"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 2" in result.stdout

        assert (tmp_path / "id_0").exists()
        assert not (tmp_path / "id_1").exists()
        assert (tmp_path / "id_2").exists()
        assert not (tmp_path / "id_3").exists()

    def test_extract_with_count(self, tmp_path: Path) -> None:
        """--countオプションで件数制限ができることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--count", "2"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 2" in result.stdout

        assert (tmp_path / "id_0").exists()
        assert (tmp_path / "id_1").exists()
        assert not (tmp_path / "id_2").exists()

    def test_extract_with_offset(self, tmp_path: Path) -> None:
        """--offsetオプションで開始位置を指定できることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--offset", "1"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 2" in result.stdout

        assert not (tmp_path / "id_0").exists()
        assert (tmp_path / "id_1").exists()
        assert (tmp_path / "id_2").exists()

    def test_extract_with_offset_and_count(self, tmp_path: Path) -> None:
        """--offsetと--countの組み合わせが正しく動作することを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
                {"id": 1, "slow": "code1_slow", "fast": "code1_fast", "slow-fast_mediTime": 200.0},
                {"id": 2, "slow": "code2_slow", "fast": "code2_fast", "slow-fast_mediTime": 300.0},
                {"id": 3, "slow": "code3_slow", "fast": "code3_fast", "slow-fast_mediTime": 400.0},
            ],
        )

        # Act - offset=1, count=2で id_1とid_2のみ抽出
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--offset", "1", "--count", "2"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 2" in result.stdout

        assert not (tmp_path / "id_0").exists()
        assert (tmp_path / "id_1").exists()
        assert (tmp_path / "id_2").exists()
        assert not (tmp_path / "id_3").exists()

    def test_extract_with_output_dir(self, tmp_path: Path) -> None:
        """--output-dirオプションで出力先を指定できることを確認"""
        # Arrange
        input_file = tmp_path / "input" / "test.jsonl"
        input_file.parent.mkdir(parents=True)
        output_dir = tmp_path / "output"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
            ],
        )

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--output-dir", str(output_dir)])

        # Assert
        assert result.exit_code == 0

        # 入力ディレクトリには作成されない
        assert not (input_file.parent / "id_0").exists()
        # 出力ディレクトリに作成される
        assert (output_dir / "id_0").exists()
        assert (output_dir / "id_0" / "slow.js").read_text() == "code0_slow"

    def test_extract_skip_existing(self, tmp_path: Path) -> None:
        """既存ディレクトリがスキップされることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "code0_slow", "fast": "code0_fast", "slow-fast_mediTime": 100.0},
            ],
        )

        # 既存ディレクトリを作成
        existing_dir = tmp_path / "id_0"
        existing_dir.mkdir()
        (existing_dir / "slow.js").write_text("existing_content")

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file)])

        # Assert
        assert result.exit_code == 0
        assert "Skipped: 1" in result.stdout

        # 既存ファイルが上書きされていないことを確認
        assert (existing_dir / "slow.js").read_text() == "existing_content"

    def test_extract_force_overwrite(self, tmp_path: Path) -> None:
        """--forceオプションで既存ファイルが上書きされることを確認"""
        # Arrange
        input_file = tmp_path / "test.jsonl"
        self._create_jsonl_file(
            input_file,
            [
                {"id": 0, "slow": "new_code", "fast": "new_fast", "slow-fast_mediTime": 100.0},
            ],
        )

        # 既存ディレクトリを作成
        existing_dir = tmp_path / "id_0"
        existing_dir.mkdir()
        (existing_dir / "slow.js").write_text("existing_content")

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file), "--force"])

        # Assert
        assert result.exit_code == 0
        assert "Created: 1" in result.stdout

        # ファイルが上書きされていることを確認
        assert (existing_dir / "slow.js").read_text() == "new_code"

    def test_extract_input_file_not_found(self, tmp_path: Path) -> None:
        """入力ファイルが存在しない場合にエラーになることを確認"""
        # Act
        result = runner.invoke(benchmark_app, ["extract", str(tmp_path / "nonexistent.jsonl")])

        # Assert
        assert result.exit_code == 1
        output = result.stdout + (result.stderr or "")
        assert "not found" in output.lower() or "error" in output.lower()

    def test_extract_empty_file(self, tmp_path: Path) -> None:
        """空のJSONLファイルが正しく処理されることを確認"""
        # Arrange
        input_file = tmp_path / "empty.jsonl"
        input_file.write_text("")

        # Act
        result = runner.invoke(benchmark_app, ["extract", str(input_file)])

        # Assert
        assert result.exit_code == 0
        assert "Created: 0" in result.stdout
        assert "Total: 0" in result.stdout
