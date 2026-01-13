"""箱ひげ図生成ライブラリのテストモジュール"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from mb_scanner.lib.visualization.boxplot import (
    create_boxplot_summary,
    load_summary_data,
)


class TestLoadSummaryData:
    """load_summary_data関数のテスト"""

    def test_load_summary_data_success(self, tmp_path: Path) -> None:
        """正常なJSONファイルからデータを読み込めること"""
        # テスト用JSONファイルを作成
        test_data = {
            "query_id": "id_10",
            "total_projects": 3,
            "results": {
                "project1": 10,
                "project2": 20,
                "project3": 5,
            },
        }
        json_file = tmp_path / "test.json"
        with json_file.open("w") as f:
            json.dump(test_data, f)

        # データを読み込み
        result = load_summary_data(json_file)

        # 検証
        assert result["query_id"] == "id_10"
        assert result["total_projects"] == 3
        assert result["values"] == [10, 20, 5]

    def test_load_summary_data_empty_results(self, tmp_path: Path) -> None:
        """空のresultsを処理できること"""
        test_data = {
            "query_id": "id_empty",
            "total_projects": 0,
            "results": {},
        }
        json_file = tmp_path / "empty.json"
        with json_file.open("w") as f:
            json.dump(test_data, f)

        result = load_summary_data(json_file)

        assert result["query_id"] == "id_empty"
        assert result["total_projects"] == 0
        assert result["values"] == []

    def test_load_summary_data_file_not_found(self, tmp_path: Path) -> None:
        """存在しないファイルに対してエラーが発生すること"""
        non_existent_file = tmp_path / "non_existent.json"

        with pytest.raises(FileNotFoundError):
            load_summary_data(non_existent_file)


class TestCreateBoxplotSummary:
    """create_boxplot_summary関数のテスト"""

    def test_create_boxplot_summary_success(self, tmp_path: Path) -> None:
        """正常な箱ひげ図生成テスト"""
        # テスト用のディレクトリとJSONファイルを作成
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_files = [
            (
                "id_10_limit_1.json",
                {"query_id": "id_10", "total_projects": 3, "results": {"p1": 10, "p2": 20, "p3": 5}},
            ),
            ("id_11_limit_1.json", {"query_id": "id_11", "total_projects": 2, "results": {"p1": 15, "p2": 25}}),
        ]

        for filename, data in test_files:
            with (input_dir / filename).open("w") as f:
                json.dump(data, f)

        output_path = tmp_path / "boxplot.png"

        # 箱ひげ図を生成
        create_boxplot_summary(input_dir, output_path)

        # ファイルが作成されたことを確認
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # matplotlibのクリーンアップ
        plt.close("all")

    def test_create_boxplot_summary_empty_directory(self, tmp_path: Path) -> None:
        """空のディレクトリに対してエラーが発生すること"""
        input_dir = tmp_path / "empty_summary"
        input_dir.mkdir()
        output_path = tmp_path / "boxplot_empty.png"

        with pytest.raises(ValueError, match="No JSON files found"):
            create_boxplot_summary(input_dir, output_path)

        plt.close("all")

    def test_create_boxplot_summary_output_directory_creation(self, tmp_path: Path) -> None:
        """出力ディレクトリの自動作成テスト"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_data = {"query_id": "id_10", "total_projects": 2, "results": {"p1": 10, "p2": 20}}
        with (input_dir / "test.json").open("w") as f:
            json.dump(test_data, f)

        # ネストされた出力パス
        nested_output_path = tmp_path / "nested" / "dir" / "boxplot.png"

        create_boxplot_summary(input_dir, nested_output_path)

        # ディレクトリが自動作成され、ファイルが存在することを確認
        assert nested_output_path.exists()
        assert nested_output_path.stat().st_size > 0

        plt.close("all")

    def test_create_boxplot_summary_single_file(self, tmp_path: Path) -> None:
        """単一のJSONファイルでの処理テスト"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_data = {"query_id": "id_10", "total_projects": 3, "results": {"p1": 10, "p2": 20, "p3": 5}}
        with (input_dir / "single.json").open("w") as f:
            json.dump(test_data, f)

        output_path = tmp_path / "boxplot_single.png"

        create_boxplot_summary(input_dir, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_boxplot_summary_with_log_scale(self, tmp_path: Path) -> None:
        """対数スケールでの箱ひげ図生成テスト"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_data = {"query_id": "id_10", "total_projects": 3, "results": {"p1": 10, "p2": 100, "p3": 1000}}
        with (input_dir / "test.json").open("w") as f:
            json.dump(test_data, f)

        output_path = tmp_path / "boxplot_log.png"

        create_boxplot_summary(input_dir, output_path, log_scale=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_boxplot_summary_without_log_scale(self, tmp_path: Path) -> None:
        """線形スケールでの箱ひげ図生成テスト（デフォルト）"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_data = {"query_id": "id_10", "total_projects": 2, "results": {"p1": 10, "p2": 20}}
        with (input_dir / "test.json").open("w") as f:
            json.dump(test_data, f)

        output_path = tmp_path / "boxplot_linear.png"

        create_boxplot_summary(input_dir, output_path, log_scale=False)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_boxplot_summary_with_query_order(self, tmp_path: Path) -> None:
        """クエリIDの順序指定テスト"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        # 3つのクエリファイルを作成
        test_files = [
            ("id_10_limit_1.json", {"query_id": "id_10", "total_projects": 2, "results": {"p1": 10, "p2": 20}}),
            ("id_18_limit_1.json", {"query_id": "id_18", "total_projects": 2, "results": {"p1": 30, "p2": 40}}),
            ("id_222_limit_1.json", {"query_id": "id_222", "total_projects": 2, "results": {"p1": 50, "p2": 60}}),
        ]

        for filename, data in test_files:
            with (input_dir / filename).open("w") as f:
                json.dump(data, f)

        output_path = tmp_path / "boxplot_ordered.png"

        # 順序を指定: id_222 -> id_10 -> id_18
        create_boxplot_summary(input_dir, output_path, query_order=["id_222", "id_10", "id_18"])

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")

    def test_create_boxplot_summary_with_partial_query_order(self, tmp_path: Path) -> None:
        """一部のクエリIDのみ指定した場合のテスト"""
        input_dir = tmp_path / "summary"
        input_dir.mkdir()

        test_files = [
            ("id_10_limit_1.json", {"query_id": "id_10", "total_projects": 2, "results": {"p1": 10, "p2": 20}}),
            ("id_18_limit_1.json", {"query_id": "id_18", "total_projects": 2, "results": {"p1": 30, "p2": 40}}),
            ("id_222_limit_1.json", {"query_id": "id_222", "total_projects": 2, "results": {"p1": 50, "p2": 60}}),
        ]

        for filename, data in test_files:
            with (input_dir / filename).open("w") as f:
                json.dump(data, f)

        output_path = tmp_path / "boxplot_partial.png"

        # 2つだけ指定（id_18は含まれない）
        create_boxplot_summary(input_dir, output_path, query_order=["id_10", "id_222"])

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        plt.close("all")
