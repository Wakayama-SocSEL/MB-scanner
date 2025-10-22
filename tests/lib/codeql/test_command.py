"""CodeQLCLIクラスのテスト"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mb_scanner.lib.codeql.command import CodeQLCLI


class TestCodeQLCLI:
    """CodeQLCLIクラスのテスト"""

    def test_analyze_database_success(self, tmp_path: Path) -> None:
        """正常にデータベースを分析できることを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Analysis successful",
                stderr="",
                returncode=0,
            )

            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
            )

            # subprocess.runが正しく呼ばれたことを確認
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]

            # コマンドの基本構造を確認
            assert args[0] == "codeql"
            assert args[1] == "database"
            assert args[2] == "analyze"
            assert str(db_path) in args
            assert "--format=sarifv2.1.0" in args
            assert f"--output={output_path}" in args
            assert "--sarif-add-snippets" in args

    def test_analyze_database_with_query_files(self, tmp_path: Path) -> None:
        """クエリファイルを指定して分析できることを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"
        query_file1 = tmp_path / "query1.ql"
        query_file2 = tmp_path / "query2.ql"
        query_file1.touch()
        query_file2.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
                query_files=[query_file1, query_file2],
            )

            args = mock_run.call_args[0][0]
            # クエリファイルがコマンドに含まれていることを確認
            assert str(query_file1) in args
            assert str(query_file2) in args

    def test_analyze_database_with_options(self, tmp_path: Path) -> None:
        """threads, ram, sarif_categoryなどのオプションが正しく反映されることを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
                threads=4,
                ram=2048,
                sarif_category="javascript",
            )

            args = mock_run.call_args[0][0]
            assert "--threads=4" in args
            assert "--ram=2048" in args
            assert "--sarif-category=javascript" in args

    def test_analyze_database_not_found(self, tmp_path: Path) -> None:
        """存在しないデータベースパスを指定した場合にFileNotFoundErrorが発生することを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "nonexistent-db"
        output_path = tmp_path / "results.sarif"

        with pytest.raises(FileNotFoundError, match="Database does not exist"):
            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
            )

    def test_analyze_database_query_file_not_found(self, tmp_path: Path) -> None:
        """存在しないクエリファイルを指定した場合にFileNotFoundErrorが発生することを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"
        nonexistent_query = tmp_path / "nonexistent.ql"

        with pytest.raises(FileNotFoundError, match="Query file does not exist"):
            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
                query_files=[nonexistent_query],
            )

    def test_analyze_database_failure(self, tmp_path: Path) -> None:
        """分析に失敗した場合にCalledProcessErrorが発生することを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["codeql", "database", "analyze"],
                stderr="Analysis failed",
            )

            with pytest.raises(subprocess.CalledProcessError):
                cli.analyze_database(
                    database_path=db_path,
                    output_path=output_path,
                )

    def test_analyze_database_timeout(self, tmp_path: Path) -> None:
        """タイムアウトした場合にTimeoutExpiredが発生することを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["codeql", "database", "analyze"],
                timeout=10,
            )

            with pytest.raises(subprocess.TimeoutExpired):
                cli.analyze_database(
                    database_path=db_path,
                    output_path=output_path,
                    timeout=10,
                )

    def test_analyze_database_without_snippets(self, tmp_path: Path) -> None:
        """sarif_add_snippets=Falseの場合、スニペットオプションが含まれないことを確認"""
        cli = CodeQLCLI()
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_path = tmp_path / "results.sarif"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            cli.analyze_database(
                database_path=db_path,
                output_path=output_path,
                sarif_add_snippets=False,
            )

            args = mock_run.call_args[0][0]
            assert "--sarif-add-snippets" not in args
