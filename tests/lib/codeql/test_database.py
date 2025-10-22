"""CodeQLDatabaseManagerクラスのテスト"""

from pathlib import Path
from unittest.mock import patch

import pytest

from mb_scanner.lib.codeql.command import CodeQLCLI
from mb_scanner.lib.codeql.database import CodeQLDatabaseManager


class TestCodeQLDatabaseManager:
    """CodeQLDatabaseManagerクラスのテスト"""

    def test_analyze_database_success(self, tmp_path: Path) -> None:
        """CodeQLDatabaseManager.analyze_databaseが正常に動作することを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        # facebook-reactのDBを作成
        db_path = base_dir / "facebook-react"
        db_path.mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        with patch.object(cli, "analyze_database") as mock_analyze:
            result_path = manager.analyze_database(
                project_full_name="facebook/react",
            )

            # analyze_databaseが呼ばれたことを確認
            mock_analyze.assert_called_once()
            call_kwargs = mock_analyze.call_args[1]

            # database_pathが正しいことを確認
            assert call_kwargs["database_path"] == db_path

            # output_pathが正しく生成されていることを確認
            expected_output = Path("outputs/queries/facebook-react/results.sarif")
            assert call_kwargs["output_path"] == expected_output
            assert result_path == expected_output

    def test_analyze_database_custom_output(self, tmp_path: Path) -> None:
        """カスタム出力パスを指定した場合に正しく動作することを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        db_path = base_dir / "facebook-react"
        db_path.mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)
        custom_output_dir = tmp_path / "custom-output"

        with patch.object(cli, "analyze_database") as mock_analyze:
            result_path = manager.analyze_database(
                project_full_name="facebook/react",
                output_dir=custom_output_dir,
            )

            call_kwargs = mock_analyze.call_args[1]
            expected_output = custom_output_dir / "results.sarif"
            assert call_kwargs["output_path"] == expected_output
            assert result_path == expected_output

    def test_analyze_database_not_exists(self, tmp_path: Path) -> None:
        """存在しないプロジェクトを指定した場合にエラーが発生することを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        # データベースが存在しないため、cli.analyze_databaseでFileNotFoundErrorが発生する
        with patch.object(cli, "analyze_database") as mock_analyze:
            mock_analyze.side_effect = FileNotFoundError("Database does not exist")

            with pytest.raises(FileNotFoundError):
                manager.analyze_database(project_full_name="nonexistent/project")

    def test_analyze_databases_parallel_success(self, tmp_path: Path) -> None:
        """複数のデータベースを並列分析できることを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        # 2つのプロジェクトのDBを作成
        (base_dir / "facebook-react").mkdir()
        (base_dir / "microsoft-vscode").mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        # cli.analyze_databaseをモックする
        with patch.object(cli, "analyze_database") as mock_cli_analyze:
            # n_jobs=1で順次実行することで、モックが正しく動作する
            results = manager.analyze_databases_parallel(
                project_full_names=["facebook/react", "microsoft/vscode"],
                n_jobs=1,  # 順次実行
            )

            # 2回呼ばれたことを確認
            assert mock_cli_analyze.call_count == 2

            # 辞書形式で結果が返されることを確認
            assert isinstance(results, dict)
            assert len(results) == 2
            assert "facebook/react" in results
            assert "microsoft/vscode" in results

    def test_analyze_databases_parallel_with_custom_jobs(self, tmp_path: Path) -> None:
        """n_jobsパラメータが正しく動作することを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        (base_dir / "facebook-react").mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        with patch.object(manager, "analyze_database") as mock_analyze:
            mock_analyze.return_value = Path("outputs/queries/facebook-react/results.sarif")

            # n_jobs=1で実行
            results = manager.analyze_databases_parallel(
                project_full_names=["facebook/react"],
                n_jobs=1,
            )

            assert mock_analyze.call_count == 1
            assert len(results) == 1

    def test_analyze_databases_parallel_empty_list(self, tmp_path: Path) -> None:
        """空のプロジェクトリストを指定した場合の動作を確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        with patch.object(manager, "analyze_database") as mock_analyze:
            results = manager.analyze_databases_parallel(
                project_full_names=[],
            )

            # analyze_databaseは呼ばれない
            mock_analyze.assert_not_called()
            # 空の辞書が返される
            assert results == {}

    def test_analyze_databases_parallel_returns_dict(self, tmp_path: Path) -> None:
        """並列分析の結果が辞書形式で返されることを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        (base_dir / "facebook-react").mkdir()
        (base_dir / "microsoft-vscode").mkdir()

        manager = CodeQLDatabaseManager(cli, base_dir)

        with patch.object(manager, "analyze_database") as mock_analyze:

            def mock_analyze_side_effect(project_full_name: str, **kwargs) -> Path:
                safe_name = project_full_name.replace("/", "-")
                return Path(f"outputs/queries/{safe_name}/results.sarif")

            mock_analyze.side_effect = mock_analyze_side_effect

            results = manager.analyze_databases_parallel(
                project_full_names=["facebook/react", "microsoft/vscode"],
            )

            # キーがプロジェクト名、値がSARIFパスであることを確認
            assert results["facebook/react"] == Path("outputs/queries/facebook-react/results.sarif")
            assert results["microsoft/vscode"] == Path("outputs/queries/microsoft-vscode/results.sarif")

    def test_analyze_database_with_query_files(self, tmp_path: Path) -> None:
        """クエリファイルを指定して分析できることを確認"""
        cli = CodeQLCLI()
        base_dir = tmp_path / "codeql-dbs"
        base_dir.mkdir()

        db_path = base_dir / "facebook-react"
        db_path.mkdir()

        query_file = tmp_path / "query.ql"
        query_file.touch()

        manager = CodeQLDatabaseManager(cli, base_dir)

        with patch.object(cli, "analyze_database") as mock_analyze:
            manager.analyze_database(
                project_full_name="facebook/react",
                query_files=[query_file],
            )

            call_kwargs = mock_analyze.call_args[1]
            assert call_kwargs["query_files"] == [query_file]
