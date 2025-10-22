"""CodeQLResultAnalyzerクラスのテスト"""

from datetime import datetime
import json
from pathlib import Path

import pytest

from mb_scanner.lib.codeql.analyzer import CodeQLResultAnalyzer


class TestCodeQLResultAnalyzer:
    """CodeQLResultAnalyzerクラスのテスト"""

    def test_count_results_success(self, tmp_path: Path) -> None:
        """SARIFファイルから正しく検出件数を取得できることを確認"""
        sarif_path = tmp_path / "results.sarif"

        # 3件の検出結果を含むSARIFファイルを作成
        sarif_data = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "CodeQL"}},
                    "results": [
                        {"ruleId": "rule1", "message": {"text": "Issue 1"}},
                        {"ruleId": "rule2", "message": {"text": "Issue 2"}},
                        {"ruleId": "rule3", "message": {"text": "Issue 3"}},
                    ],
                }
            ],
        }

        sarif_path.write_text(json.dumps(sarif_data))

        analyzer = CodeQLResultAnalyzer()
        count = analyzer.count_results(sarif_path)

        assert count == 3

    def test_count_results_zero(self, tmp_path: Path) -> None:
        """検出0件の場合も正しく処理できることを確認"""
        sarif_path = tmp_path / "results.sarif"

        sarif_data = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "CodeQL"}},
                    "results": [],
                }
            ],
        }

        sarif_path.write_text(json.dumps(sarif_data))

        analyzer = CodeQLResultAnalyzer()
        count = analyzer.count_results(sarif_path)

        assert count == 0

    def test_count_results_file_not_found(self, tmp_path: Path) -> None:
        """存在しないSARIFファイルを指定した場合にFileNotFoundErrorが発生することを確認"""
        sarif_path = tmp_path / "nonexistent.sarif"

        analyzer = CodeQLResultAnalyzer()

        with pytest.raises(FileNotFoundError):
            analyzer.count_results(sarif_path)

    def test_count_results_invalid_format(self, tmp_path: Path) -> None:
        """不正なSARIF形式の場合にValueErrorが発生することを確認"""
        sarif_path = tmp_path / "invalid.sarif"
        sarif_path.write_text("invalid json")

        analyzer = CodeQLResultAnalyzer()

        with pytest.raises(ValueError, match="Invalid SARIF format"):
            analyzer.count_results(sarif_path)

    def test_count_results_missing_runs(self, tmp_path: Path) -> None:
        """runsキーが存在しない場合にValueErrorが発生することを確認"""
        sarif_path = tmp_path / "no_runs.sarif"
        sarif_data = {"version": "2.1.0"}
        sarif_path.write_text(json.dumps(sarif_data))

        analyzer = CodeQLResultAnalyzer()

        with pytest.raises(ValueError, match="Invalid SARIF format"):
            analyzer.count_results(sarif_path)

    def test_filter_projects_by_threshold(self, tmp_path: Path) -> None:
        """閾値以上のプロジェクトが正しくフィルタリングされることを確認"""
        # 3つのSARIFファイルを作成（検出件数: 5, 10, 15）
        results_dict: dict[str, Path] = {}

        for project_name, count in [("project-a", 5), ("project-b", 10), ("project-c", 15)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))
            results_dict[project_name] = sarif_path

        analyzer = CodeQLResultAnalyzer()

        # 閾値10: project-bとproject-cが選ばれる
        filtered = analyzer.filter_projects_by_threshold(results_dict, threshold=10)
        assert set(filtered) == {"project-b", "project-c"}

        # 閾値15: project-cのみが選ばれる
        filtered = analyzer.filter_projects_by_threshold(results_dict, threshold=15)
        assert filtered == ["project-c"]

        # 閾値5: 全て選ばれる
        filtered = analyzer.filter_projects_by_threshold(results_dict, threshold=5)
        assert set(filtered) == {"project-a", "project-b", "project-c"}

        # 閾値16: どれも選ばれない
        filtered = analyzer.filter_projects_by_threshold(results_dict, threshold=16)
        assert filtered == []

    def test_get_summary(self, tmp_path: Path) -> None:
        """全プロジェクトの検出件数サマリーが正しく取得できることを確認"""
        results_dict: dict[str, Path] = {}

        for project_name, count in [("project-a", 5), ("project-b", 10), ("project-c", 0)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))
            results_dict[project_name] = sarif_path

        analyzer = CodeQLResultAnalyzer()
        summary = analyzer.get_summary(results_dict)

        assert summary == {
            "project-a": 5,
            "project-b": 10,
            "project-c": 0,
        }

    def test_get_summary_sorted_descending(self, tmp_path: Path) -> None:
        """検出件数で降順ソートされたサマリーが正しく取得できることを確認"""
        results_dict: dict[str, Path] = {}

        for project_name, count in [("project-a", 5), ("project-b", 15), ("project-c", 10)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))
            results_dict[project_name] = sarif_path

        analyzer = CodeQLResultAnalyzer()
        sorted_summary = analyzer.get_summary_sorted(results_dict, reverse=True)

        assert sorted_summary == [
            ("project-b", 15),
            ("project-c", 10),
            ("project-a", 5),
        ]

    def test_get_summary_sorted_ascending(self, tmp_path: Path) -> None:
        """検出件数で昇順ソートされたサマリーが正しく取得できることを確認"""
        results_dict: dict[str, Path] = {}

        for project_name, count in [("project-a", 5), ("project-b", 15), ("project-c", 10)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))
            results_dict[project_name] = sarif_path

        analyzer = CodeQLResultAnalyzer()
        sorted_summary = analyzer.get_summary_sorted(results_dict, reverse=False)

        assert sorted_summary == [
            ("project-a", 5),
            ("project-c", 10),
            ("project-b", 15),
        ]

    def test_save_summary_json_without_threshold(self, tmp_path: Path) -> None:
        """閾値なしでサマリーJSONが正しく保存されることを確認"""
        # Arrange
        output_path = tmp_path / "summary.json"
        query_id = "id_10"
        results = {
            "facebook/react": 15,
            "microsoft/vscode": 8,
        }

        # Act
        analyzer = CodeQLResultAnalyzer()
        analyzer.save_summary_json(query_id, results, output_path)

        # Assert
        assert output_path.exists()

        with output_path.open() as f:
            saved_data = json.load(f)

        assert saved_data["query_id"] == "id_10"
        assert saved_data["total_projects"] == 2
        assert saved_data["results"] == results
        assert "threshold" not in saved_data
        assert "generated_at" in saved_data

        # ISO 8601形式の検証
        datetime.fromisoformat(saved_data["generated_at"].replace("Z", "+00:00"))

    def test_save_summary_json_with_threshold(self, tmp_path: Path) -> None:
        """閾値ありでサマリーJSONが正しく保存されることを確認"""
        # Arrange
        output_path = tmp_path / "limit_10_summary.json"
        query_id = "id_10"
        results = {
            "facebook/react": 15,
            "microsoft/vscode": 12,
        }
        threshold = 10

        # Act
        analyzer = CodeQLResultAnalyzer()
        analyzer.save_summary_json(query_id, results, output_path, threshold=threshold)

        # Assert
        assert output_path.exists()

        with output_path.open() as f:
            saved_data = json.load(f)

        assert saved_data["query_id"] == "id_10"
        assert saved_data["threshold"] == 10
        assert saved_data["total_projects"] == 2
        assert saved_data["results"] == results
        assert "generated_at" in saved_data

    def test_save_summary_json_empty_results(self, tmp_path: Path) -> None:
        """結果が0件でも正しく保存されることを確認"""
        # Arrange
        output_path = tmp_path / "summary.json"
        query_id = "id_10"
        results: dict[str, int] = {}

        # Act
        analyzer = CodeQLResultAnalyzer()
        analyzer.save_summary_json(query_id, results, output_path)

        # Assert
        assert output_path.exists()

        with output_path.open() as f:
            saved_data = json.load(f)

        assert saved_data["total_projects"] == 0
        assert saved_data["results"] == {}

    def test_save_summary_json_creates_parent_directory(self, tmp_path: Path) -> None:
        """親ディレクトリが存在しない場合も作成されることを確認"""
        # Arrange
        output_path = tmp_path / "subdir" / "nested" / "summary.json"
        query_id = "id_10"
        results = {"facebook/react": 15}

        # Act
        analyzer = CodeQLResultAnalyzer()
        analyzer.save_summary_json(query_id, results, output_path)

        # Assert
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_generate_summary_from_directory_without_threshold(self, tmp_path: Path) -> None:
        """ディレクトリ内のSARIFファイルから結果を集計（閾値なし）することを確認"""
        # Arrange - SARIFファイルを作成
        for project_name, count in [("facebook-react", 15), ("microsoft-vscode", 8)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))

        # Act
        analyzer = CodeQLResultAnalyzer()
        summary = analyzer.generate_summary_from_directory(tmp_path)

        # Assert
        assert summary == {
            "facebook/react": 15,
            "microsoft/vscode": 8,
        }

    def test_generate_summary_from_directory_with_threshold(self, tmp_path: Path) -> None:
        """閾値でフィルタリングされることを確認"""
        # Arrange - SARIFファイルを作成
        for project_name, count in [("facebook-react", 15), ("microsoft-vscode", 8)]:
            sarif_path = tmp_path / f"{project_name}.sarif"
            sarif_data = {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {"driver": {"name": "CodeQL"}},
                        "results": [{"ruleId": f"rule{i}"} for i in range(count)],
                    }
                ],
            }
            sarif_path.write_text(json.dumps(sarif_data))

        # Act
        analyzer = CodeQLResultAnalyzer()
        summary = analyzer.generate_summary_from_directory(tmp_path, threshold=10)

        # Assert - 8件のmicrosoft/vscodeは除外される
        assert summary == {
            "facebook/react": 15,
        }

    def test_generate_summary_from_directory_empty(self, tmp_path: Path) -> None:
        """SARIFファイルが存在しない場合に空の辞書が返ることを確認"""
        # Arrange - 空のディレクトリ

        # Act
        analyzer = CodeQLResultAnalyzer()
        summary = analyzer.generate_summary_from_directory(tmp_path)

        # Assert
        assert summary == {}

    def test_generate_summary_from_directory_nonexistent(self, tmp_path: Path) -> None:
        """ディレクトリが存在しない場合にFileNotFoundErrorが発生することを確認"""
        # Arrange
        nonexistent_dir = tmp_path / "nonexistent"

        # Act & Assert
        analyzer = CodeQLResultAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.generate_summary_from_directory(nonexistent_dir)
