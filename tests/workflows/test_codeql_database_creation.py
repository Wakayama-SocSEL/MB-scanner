"""CodeQLDatabaseCreationWorkflowのテスト"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

from mb_scanner.lib.codeql.database import CodeQLDatabaseManager
from mb_scanner.lib.github.clone import RepositoryCloner
from mb_scanner.workflows.codeql_database_creation import CodeQLDatabaseCreationWorkflow


class TestCodeQLDatabaseCreationWorkflow:
    """CodeQLDatabaseCreationWorkflowのテスト"""

    def test_create_database_for_project_success(self, tmp_path: Path) -> None:
        """データベース作成が成功し、クローンディレクトリが削除されない（残存する）ことを確認"""
        # Arrange
        clone_base_dir = tmp_path / "clones"
        clone_path = clone_base_dir / "facebook-react"

        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_cloner.clone.return_value = clone_path

        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = False
        mock_db_manager.create_database.return_value = tmp_path / "db" / "facebook-react"

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=clone_base_dir,
        )

        # Act
        result = workflow.create_database_for_project(
            project_full_name="facebook/react",
            repository_url="https://github.com/facebook/react.git",
            language="javascript",
            skip_if_exists=False,
            force=False,
        )

        # Assert
        assert result["status"] == "created"
        assert result["db_path"] == str(tmp_path / "db" / "facebook-react")

        # クローンが呼ばれたことを確認
        mock_cloner.clone.assert_called_once_with(
            "https://github.com/facebook/react.git",
            clone_path,
            skip_if_exists=True,
        )

        # データベース作成が呼ばれたことを確認
        mock_db_manager.create_database.assert_called_once_with(
            project_full_name="facebook/react",
            source_root=clone_path,
            language="javascript",
            force=False,
        )

    def test_create_database_for_project_skip_existing_clone(self, tmp_path: Path) -> None:
        """既存のクローンがある場合、再クローンせずに進むことを確認"""
        # Arrange
        clone_base_dir = tmp_path / "clones"
        existing_clone_path = clone_base_dir / "facebook-react"
        existing_clone_path.mkdir(parents=True)  # 既存クローンをシミュレート

        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_cloner.clone.return_value = existing_clone_path  # 既存パスを返す

        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = False
        mock_db_manager.create_database.return_value = tmp_path / "db" / "facebook-react"

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=clone_base_dir,
        )

        # Act
        result = workflow.create_database_for_project(
            project_full_name="facebook/react",
            repository_url="https://github.com/facebook/react.git",
            language="javascript",
            skip_if_exists=False,
            force=False,
        )

        # Assert
        assert result["status"] == "created"

        # skip_if_exists=True でクローンが呼ばれたことを確認
        mock_cloner.clone.assert_called_once_with(
            "https://github.com/facebook/react.git",
            existing_clone_path,
            skip_if_exists=True,
        )

    def test_create_database_for_project_skip_if_exists(self, tmp_path: Path) -> None:
        """既存DBがある場合スキップすることを確認"""
        # Arrange
        clone_base_dir = tmp_path / "clones"

        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = True
        mock_db_manager.get_database_path.return_value = tmp_path / "db" / "facebook-react"

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=clone_base_dir,
        )

        # Act
        result = workflow.create_database_for_project(
            project_full_name="facebook/react",
            repository_url="https://github.com/facebook/react.git",
            language="javascript",
            skip_if_exists=True,
            force=False,
        )

        # Assert
        assert result["status"] == "skipped"
        assert result["db_path"] == str(tmp_path / "db" / "facebook-react")

        # クローンもDB作成も呼ばれないことを確認
        mock_cloner.clone.assert_not_called()
        mock_db_manager.create_database.assert_not_called()

    def test_create_database_for_project_clone_failure(self, tmp_path: Path) -> None:
        """クローンに失敗した場合にエラーが返されることを確認"""
        # Arrange
        clone_base_dir = tmp_path / "clones"

        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_cloner.clone.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "clone"],
            stderr="fatal: repository not found",
        )

        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = False

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=clone_base_dir,
        )

        # Act
        result = workflow.create_database_for_project(
            project_full_name="facebook/react",
            repository_url="https://github.com/facebook/react.git",
            language="javascript",
            skip_if_exists=False,
            force=False,
        )

        # Assert
        assert result["status"] == "error"
        assert "returned non-zero exit status" in result["error"]

        # DB作成は呼ばれないことを確認
        mock_db_manager.create_database.assert_not_called()

    def test_create_database_for_project_database_creation_failure(self, tmp_path: Path) -> None:
        """データベース作成に失敗した場合にエラーが返されることを確認"""
        # Arrange
        clone_base_dir = tmp_path / "clones"
        clone_path = clone_base_dir / "facebook-react"

        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_cloner.clone.return_value = clone_path

        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)
        mock_db_manager.database_exists.return_value = False
        mock_db_manager.create_database.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["codeql", "database", "create"],
            stderr="Database creation failed",
        )

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=clone_base_dir,
        )

        # Act
        result = workflow.create_database_for_project(
            project_full_name="facebook/react",
            repository_url="https://github.com/facebook/react.git",
            language="javascript",
            skip_if_exists=False,
            force=False,
        )

        # Assert
        assert result["status"] == "error"
        assert "returned non-zero exit status" in result["error"]

    def test_create_databases_batch(self, tmp_path: Path) -> None:
        """バッチ処理が正しく動作することを確認"""
        # Arrange
        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=tmp_path / "clones",
        )

        projects = [
            (1, "facebook/react", "https://github.com/facebook/react.git"),
            (2, "microsoft/vscode", "https://github.com/microsoft/vscode.git"),
        ]

        # Act
        with patch.object(workflow, "create_database_for_project") as mock_create:
            mock_create.side_effect = [
                {"status": "created", "db_path": "/path/to/db1"},
                {"status": "created", "db_path": "/path/to/db2"},
            ]

            stats = workflow.create_databases_batch(
                projects=projects,
                language="javascript",
                skip_if_exists=True,
                force=False,
            )

        # Assert
        assert stats["total"] == 2
        assert stats["created"] == 2
        assert stats["skipped"] == 0
        assert stats["failed"] == 0
        assert mock_create.call_count == 2

    def test_create_databases_batch_partial_failure(self, tmp_path: Path) -> None:
        """一部のプロジェクトが失敗しても継続することを確認"""
        # Arrange
        mock_cloner = MagicMock(spec=RepositoryCloner)
        mock_db_manager = MagicMock(spec=CodeQLDatabaseManager)

        workflow = CodeQLDatabaseCreationWorkflow(
            cloner=mock_cloner,
            db_manager=mock_db_manager,
            clone_base_dir=tmp_path / "clones",
        )

        projects = [
            (1, "facebook/react", "https://github.com/facebook/react.git"),
            (2, "microsoft/vscode", "https://github.com/microsoft/vscode.git"),
            (3, "nodejs/node", "https://github.com/nodejs/node.git"),
        ]

        # Act
        with patch.object(workflow, "create_database_for_project") as mock_create:
            mock_create.side_effect = [
                {"status": "created", "db_path": "/path/to/db1"},
                {"status": "error", "error": "Clone failed"},
                {"status": "skipped", "db_path": "/path/to/db3"},
            ]

            stats = workflow.create_databases_batch(
                projects=projects,
                language="javascript",
                skip_if_exists=True,
                force=False,
            )

        # Assert
        assert stats["total"] == 3
        assert stats["created"] == 1
        assert stats["skipped"] == 1
        assert stats["failed"] == 1
