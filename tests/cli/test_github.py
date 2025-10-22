"""tests/cli/test_github.py - GitHub CLI コマンドのテスト"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from mb_scanner.cli import app

runner = CliRunner()


class TestGitHubRateLimitCommand:
    """GitHub rate-limitコマンドのテスト"""

    @patch("mb_scanner.cli.github.GitHubClient")
    def test_rate_limit_ok(self, mock_client_class: MagicMock) -> None:
        """正常なレート制限状態のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        reset_time = datetime.now(UTC) + timedelta(hours=1)
        mock_client.get_rate_limit_info.return_value = {
            "limit": 5000,
            "remaining": 4500,
            "reset_time": reset_time,
            "wait_time_seconds": 0,
        }

        # コマンド実行
        result = runner.invoke(app, ["github", "rate-limit"])

        # 検証
        assert result.exit_code == 0
        assert "GitHub API Rate Limit Status" in result.stdout
        assert "5000 requests/hour" in result.stdout
        assert "4500 requests" in result.stdout
        assert "✓ OK" in result.stdout

    @patch("mb_scanner.cli.github.GitHubClient")
    def test_rate_limit_warning(self, mock_client_class: MagicMock) -> None:
        """残りが少ない状態のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        reset_time = datetime.now(UTC) + timedelta(hours=1)
        mock_client.get_rate_limit_info.return_value = {
            "limit": 5000,
            "remaining": 500,  # 10%しか残っていない
            "reset_time": reset_time,
            "wait_time_seconds": 0,
        }

        # コマンド実行
        result = runner.invoke(app, ["github", "rate-limit"])

        # 検証
        assert result.exit_code == 0
        assert "⚠ WARNING" in result.stdout
        assert "500 requests" in result.stdout

    @patch("mb_scanner.cli.github.GitHubClient")
    def test_rate_limit_exceeded(self, mock_client_class: MagicMock) -> None:
        """レート制限超過のテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        reset_time = datetime.now(UTC) + timedelta(minutes=30)
        mock_client.get_rate_limit_info.return_value = {
            "limit": 5000,
            "remaining": 0,
            "reset_time": reset_time,
            "wait_time_seconds": 1800,  # 30分
        }

        # コマンド実行
        result = runner.invoke(app, ["github", "rate-limit"])

        # 検証
        assert result.exit_code == 0
        assert "✗ RATE LIMITED" in result.stdout
        assert "0 requests" in result.stdout
        assert "30 minutes" in result.stdout

    @patch("mb_scanner.cli.github.GitHubClient")
    def test_rate_limit_error(self, mock_client_class: MagicMock) -> None:
        """エラーハンドリングのテスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_rate_limit_info.side_effect = Exception("API Error")

        # コマンド実行
        result = runner.invoke(app, ["github", "rate-limit"])

        # 検証
        assert result.exit_code == 1
        assert "Error:" in result.stdout
        assert "API Error" in result.stdout


class TestGitHubCloneCommand:
    """GitHub cloneコマンドのテスト"""

    def test_clone_command(self, tmp_path: Path) -> None:
        """cloneコマンドが正しく動作することを確認"""

        # クローン時にディレクトリを作成する副作用
        def create_clone_dir(url, destination, **kwargs):
            destination.mkdir(parents=True, exist_ok=True)
            return destination

        # Act
        with (
            patch("mb_scanner.cli.github.SessionLocal") as mock_session_local,
            patch("mb_scanner.cli.github.ProjectService") as mock_project_service,
            patch("mb_scanner.cli.github.RepositoryCloner") as mock_cloner_class,
            patch("mb_scanner.cli.github.settings") as mock_settings,
        ):
            # DB設定
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db

            # ProjectService設定
            mock_service = MagicMock()
            mock_service.get_all_project_urls.return_value = [
                (1, "facebook/react", "https://github.com/facebook/react.git"),
                (2, "microsoft/vscode", "https://github.com/microsoft/vscode.git"),
            ]
            mock_project_service.return_value = mock_service

            # Cloner設定
            mock_cloner = MagicMock()
            mock_cloner.clone.side_effect = create_clone_dir
            mock_cloner_class.return_value = mock_cloner

            # Settings設定
            mock_settings.github_token = "test_token"
            mock_settings.effective_codeql_clone_dir = tmp_path / "clones"

            result = runner.invoke(app, ["github", "clone"])

        # Assert
        assert result.exit_code == 0
        assert "2 projects" in result.stdout
        assert "Success: 2" in result.stdout

        # クローナーが正しく呼ばれたことを確認
        assert mock_cloner.clone.call_count == 2

    def test_clone_command_with_max_projects(self, tmp_path: Path) -> None:
        """--max-projectsオプションが正しく動作することを確認"""

        # クローン時にディレクトリを作成する副作用
        def create_clone_dir(url, destination, **kwargs):
            destination.mkdir(parents=True, exist_ok=True)
            return destination

        # Act
        with (
            patch("mb_scanner.cli.github.SessionLocal") as mock_session_local,
            patch("mb_scanner.cli.github.ProjectService") as mock_project_service,
            patch("mb_scanner.cli.github.RepositoryCloner") as mock_cloner_class,
            patch("mb_scanner.cli.github.settings") as mock_settings,
        ):
            # DB設定
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db

            # ProjectService設定
            mock_service = MagicMock()
            mock_service.get_all_project_urls.return_value = [
                (1, "facebook/react", "https://github.com/facebook/react.git"),
                (2, "microsoft/vscode", "https://github.com/microsoft/vscode.git"),
                (3, "nodejs/node", "https://github.com/nodejs/node.git"),
            ]
            mock_project_service.return_value = mock_service

            # Cloner設定
            mock_cloner = MagicMock()
            mock_cloner.clone.side_effect = create_clone_dir
            mock_cloner_class.return_value = mock_cloner

            # Settings設定
            mock_settings.github_token = "test_token"
            mock_settings.effective_codeql_clone_dir = tmp_path / "clones"

            result = runner.invoke(app, ["github", "clone", "--max-projects", "2"])

        # Assert
        assert result.exit_code == 0
        assert "2 projects" in result.stdout

        # 2つのプロジェクトのみクローンされることを確認
        assert mock_cloner.clone.call_count == 2

    def test_clone_command_with_force(self, tmp_path: Path) -> None:
        """--forceオプションで既存リポジトリが削除されることを確認"""
        # Arrange
        clone_dir = tmp_path / "clones"
        existing_repo = clone_dir / "facebook-react"
        existing_repo.mkdir(parents=True)

        # Act
        with (
            patch("mb_scanner.cli.github.SessionLocal") as mock_session_local,
            patch("mb_scanner.cli.github.ProjectService") as mock_project_service,
            patch("mb_scanner.cli.github.RepositoryCloner") as mock_cloner_class,
            patch("mb_scanner.cli.github.settings") as mock_settings,
            patch("mb_scanner.cli.github.cleanup_directory") as mock_cleanup,
        ):
            # DB設定
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db

            # ProjectService設定
            mock_service = MagicMock()
            mock_service.get_all_project_urls.return_value = [
                (1, "facebook/react", "https://github.com/facebook/react.git"),
            ]
            mock_project_service.return_value = mock_service

            # Cloner設定
            mock_cloner = MagicMock()
            mock_cloner_class.return_value = mock_cloner

            # Settings設定
            mock_settings.github_token = "test_token"
            mock_settings.effective_codeql_clone_dir = clone_dir

            result = runner.invoke(app, ["github", "clone", "--force"])

        # Assert
        assert result.exit_code == 0

        # cleanup_directoryが呼ばれたことを確認
        mock_cleanup.assert_called()

    def test_clone_command_no_projects(self, tmp_path: Path) -> None:
        """プロジェクトが存在しない場合の動作を確認"""
        # Act
        with (
            patch("mb_scanner.cli.github.SessionLocal") as mock_session_local,
            patch("mb_scanner.cli.github.ProjectService") as mock_project_service,
            patch("mb_scanner.cli.github.settings") as mock_settings,
        ):
            # DB設定
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db

            # ProjectService設定
            mock_service = MagicMock()
            mock_service.get_all_project_urls.return_value = []
            mock_project_service.return_value = mock_service

            # Settings設定
            mock_settings.effective_codeql_clone_dir = tmp_path / "clones"

            result = runner.invoke(app, ["github", "clone"])

        # Assert
        assert result.exit_code == 0
        assert "No projects found" in result.stdout
