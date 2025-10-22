"""CodeQLQueryExecutionWorkflowのテスト"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

from mb_scanner.lib.codeql.command import CodeQLCLI
from mb_scanner.lib.codeql.database import CodeQLDatabaseManager
from mb_scanner.workflows.codeql_query_execution import CodeQLQueryExecutionWorkflow


class TestCodeQLQueryExecutionWorkflow:
    """CodeQLQueryExecutionWorkflowのテスト"""

    def test_execute_query_for_project_success(self, tmp_path: Path) -> None:
        """正常にクエリを実行できることを確認"""
        # Arrange
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_base_dir = tmp_path / "outputs"
        query_file = tmp_path / "id_10.ql"
        query_file.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = True
        mock_db_manager.get_database_path.return_value = db_path

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        with patch("mb_scanner.workflows.codeql_query_execution.CodeQLResultAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.count_results.return_value = 42
            result = workflow.execute_query_for_project(
                project_full_name="facebook/react",
                query_files=[query_file],
                output_base_dir=output_base_dir,
            )

        # Assert
        assert result["status"] == "success"
        assert len(result["results"]) == 1
        assert result["results"][0]["query_file"] == "id_10.ql"
        assert result["results"][0]["result_count"] == 42
        mock_db_manager.database_exists.assert_called_once_with("facebook/react")
        mock_cli.analyze_database.assert_called_once()

    def test_execute_query_for_project_multiple_queries(self, tmp_path: Path) -> None:
        """複数のクエリファイルが正常に実行できることを確認"""
        # Arrange
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_base_dir = tmp_path / "outputs"
        query_file1 = tmp_path / "id_10.ql"
        query_file2 = tmp_path / "id_20.ql"
        query_file1.touch()
        query_file2.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = True
        mock_db_manager.get_database_path.return_value = db_path

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        with patch("mb_scanner.workflows.codeql_query_execution.CodeQLResultAnalyzer") as mock_analyzer:
            mock_analyzer.return_value.count_results.side_effect = [10, 20]
            result = workflow.execute_query_for_project(
                project_full_name="facebook/react",
                query_files=[query_file1, query_file2],
                output_base_dir=output_base_dir,
            )

        # Assert
        assert result["status"] == "success"
        assert len(result["results"]) == 2
        assert result["results"][0]["query_file"] == "id_10.ql"
        assert result["results"][0]["result_count"] == 10
        assert result["results"][1]["query_file"] == "id_20.ql"
        assert result["results"][1]["result_count"] == 20
        assert mock_cli.analyze_database.call_count == 2

    def test_execute_query_for_project_database_not_found(self, tmp_path: Path) -> None:
        """データベースが存在しない場合にエラーが返されることを確認"""
        # Arrange
        output_base_dir = tmp_path / "outputs"
        query_file = tmp_path / "test.ql"
        query_file.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = False

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        result = workflow.execute_query_for_project(
            project_full_name="facebook/react",
            query_files=[query_file],
            output_base_dir=output_base_dir,
        )

        # Assert
        assert result["status"] == "error"
        assert "Database does not exist" in result["error"]
        mock_cli.analyze_database.assert_not_called()

    def test_execute_query_for_project_query_file_not_found(self, tmp_path: Path) -> None:
        """クエリファイルが存在しない場合にエラーが返されることを確認"""
        # Arrange
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_base_dir = tmp_path / "outputs"
        nonexistent_query = tmp_path / "nonexistent.ql"

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = True
        mock_db_manager.get_database_path.return_value = db_path

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        result = workflow.execute_query_for_project(
            project_full_name="facebook/react",
            query_files=[nonexistent_query],
            output_base_dir=output_base_dir,
        )

        # Assert
        assert result["status"] == "error"
        assert "Query file does not exist" in result["error"]
        mock_cli.analyze_database.assert_not_called()

    def test_execute_query_for_project_analysis_failure(self, tmp_path: Path) -> None:
        """クエリ実行に失敗した場合にエラーが返されることを確認"""
        # Arrange
        db_path = tmp_path / "test-db"
        db_path.mkdir()
        output_base_dir = tmp_path / "outputs"
        query_file = tmp_path / "test.ql"
        query_file.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_cli.analyze_database.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["codeql", "database", "analyze"],
            stderr="Analysis failed",
        )

        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = True
        mock_db_manager.get_database_path.return_value = db_path

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        result = workflow.execute_query_for_project(
            project_full_name="facebook/react",
            query_files=[query_file],
            output_base_dir=output_base_dir,
        )

        # Assert
        assert result["status"] == "error"
        assert "returned non-zero exit status" in result["error"]

    def test_execute_queries_batch_success(self, tmp_path: Path) -> None:
        """複数プロジェクトで正常に実行できることを確認"""
        # Arrange
        query_file = tmp_path / "test.ql"
        query_file.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        with patch.object(workflow, "execute_query_for_project") as mock_execute:
            mock_execute.return_value = {"status": "success", "results": []}

            stats = workflow.execute_queries_batch(
                projects=["facebook/react", "microsoft/vscode"],
                query_files=[query_file],
                output_base_dir=tmp_path,
            )

        # Assert
        assert stats["total"] == 2
        assert stats["success"] == 2
        assert stats["failed"] == 0
        assert mock_execute.call_count == 2

    def test_execute_queries_batch_partial_failure(self, tmp_path: Path) -> None:
        """一部のプロジェクトが失敗しても継続することを確認"""
        # Arrange
        query_file = tmp_path / "test.ql"
        query_file.touch()

        mock_cli = MagicMock(spec=CodeQLCLI)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)

        workflow = CodeQLQueryExecutionWorkflow(
            codeql_cli=mock_cli,
            db_manager=mock_db_manager,
        )

        # Act
        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"status": "success", "results": []}
            return {"status": "error", "error": "Test error"}

        with patch.object(workflow, "execute_query_for_project", side_effect=mock_execute):
            stats = workflow.execute_queries_batch(
                projects=["facebook/react", "microsoft/vscode"],
                query_files=[query_file],
                output_base_dir=tmp_path,
            )

        # Assert
        assert stats["total"] == 2
        assert stats["success"] == 1
        assert stats["failed"] == 1
