"""CodeQL CLIコマンドのテスト"""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mb_scanner.cli.codeql import codeql_app

runner = CliRunner()


class TestCodeQLSummaryCommand:
    """mb-scanner codeql summaryコマンドのテスト"""

    def test_summary_without_threshold(self, tmp_path: Path) -> None:
        """閾値なしでサマリーが正しく生成されることを確認"""
        # Arrange - SARIFファイルを作成
        # effective_codeql_output_dirはoutputs/queriesに相当するため、tmp_pathをそれとして扱う
        query_dir = tmp_path / "id_10"
        query_dir.mkdir(parents=True)

        for project_name, count in [("facebook-react", 15), ("microsoft-vscode", 8)]:
            sarif_path = query_dir / f"{project_name}.sarif"
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

        # Act - settingsをモックして出力ディレクトリを設定
        with patch("mb_scanner.cli.codeql.settings") as mock_settings:
            mock_settings.effective_codeql_output_dir = tmp_path
            result = runner.invoke(codeql_app, ["summary", "id_10"])

        # Assert
        assert result.exit_code == 0
        assert "Successfully generated summary" in result.stdout

        # サマリーファイルが存在することを確認
        summary_path = query_dir / "summary.json"
        assert summary_path.exists()

        with summary_path.open() as f:
            summary_data = json.load(f)

        assert summary_data["query_id"] == "id_10"
        assert summary_data["total_projects"] == 2
        assert summary_data["results"] == {
            "facebook/react": 15,
            "microsoft/vscode": 8,
        }
        assert "threshold" not in summary_data

    def test_summary_with_threshold(self, tmp_path: Path) -> None:
        """閾値ありでサマリーが正しく生成されることを確認"""
        # Arrange - SARIFファイルを作成
        query_dir = tmp_path / "id_10"
        query_dir.mkdir(parents=True)

        for project_name, count in [("facebook-react", 15), ("microsoft-vscode", 8)]:
            sarif_path = query_dir / f"{project_name}.sarif"
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
        with patch("mb_scanner.cli.codeql.settings") as mock_settings:
            mock_settings.effective_codeql_output_dir = tmp_path
            result = runner.invoke(codeql_app, ["summary", "id_10", "--threshold", "10"])

        # Assert
        assert result.exit_code == 0

        # サマリーファイルが存在することを確認
        summary_path = query_dir / "limit_10_summary.json"
        assert summary_path.exists()

        with summary_path.open() as f:
            summary_data = json.load(f)

        assert summary_data["query_id"] == "id_10"
        assert summary_data["threshold"] == 10
        assert summary_data["total_projects"] == 1
        # 閾値10以上なので、facebook/reactのみ
        assert summary_data["results"] == {
            "facebook/react": 15,
        }

    def test_summary_query_directory_not_found(self, tmp_path: Path) -> None:
        """クエリディレクトリが存在しない場合にエラーになることを確認"""
        # Arrange - 空のディレクトリ

        # Act
        with patch("mb_scanner.cli.codeql.settings") as mock_settings:
            mock_settings.effective_codeql_output_dir = tmp_path
            result = runner.invoke(codeql_app, ["summary", "id_999"])

        # Assert
        assert result.exit_code == 1
        # エラーメッセージは標準エラー出力に出力される
        output = result.stdout + (result.stderr or "")
        assert "does not exist" in output or "not found" in output.lower()

    def test_summary_custom_output_dir(self, tmp_path: Path) -> None:
        """カスタム出力ディレクトリが指定できることを確認"""
        # Arrange - SARIFファイルを作成
        # カスタムディレクトリがoutputs/queriesに相当する
        custom_dir = tmp_path / "custom"
        query_dir = custom_dir / "id_10"
        query_dir.mkdir(parents=True)

        sarif_path = query_dir / "facebook-react.sarif"
        sarif_data = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "CodeQL"}},
                    "results": [{"ruleId": "rule1"}],
                }
            ],
        }
        sarif_path.write_text(json.dumps(sarif_data))

        # Act
        result = runner.invoke(codeql_app, ["summary", "id_10", "--output-dir", str(custom_dir)])

        # Assert
        assert result.exit_code == 0

        summary_path = query_dir / "summary.json"
        assert summary_path.exists()
