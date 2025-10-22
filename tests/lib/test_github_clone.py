"""RepositoryClonerクラスのテスト"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mb_scanner.lib.github.clone import RepositoryCloner


class TestRepositoryCloner:
    """RepositoryClonerクラスのテスト"""

    def test_clone_success(self, tmp_path: Path) -> None:
        """正常にリポジトリをクローンできることを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Cloning successful",
                stderr="",
                returncode=0,
            )

            result = cloner.clone(repo_url, destination)

            # 正しいパスが返されることを確認
            assert result == destination

            # subprocess.runが正しく呼ばれたことを確認
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]

            # コマンドの基本構造を確認
            assert args[0] == "git"
            assert args[1] == "clone"
            assert args[2] == "--depth=1"
            assert args[3] == repo_url
            assert args[4] == str(destination)

    def test_clone_with_custom_depth(self, tmp_path: Path) -> None:
        """カスタムdepthでクローンできることを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            cloner.clone(repo_url, destination, depth=5)

            args = mock_run.call_args[0][0]
            assert args[2] == "--depth=5"

    def test_clone_destination_already_exists_without_skip(self, tmp_path: Path) -> None:
        """skip_if_exists=Falseで既存ディレクトリがある場合、ValueErrorが発生することを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"
        destination.mkdir()  # 既存ディレクトリを作成

        with pytest.raises(ValueError, match="Destination directory already exists"):
            cloner.clone(repo_url, destination, skip_if_exists=False)

    def test_clone_destination_already_exists_with_skip(self, tmp_path: Path) -> None:
        """skip_if_exists=Trueで既存ディレクトリがある場合、そのパスを返すことを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"
        destination.mkdir()  # 既存ディレクトリを作成

        # モックは呼ばれないことを確認するため
        with patch("subprocess.run") as mock_run:
            result = cloner.clone(repo_url, destination, skip_if_exists=True)

            # 既存のパスが返されることを確認
            assert result == destination
            # git cloneは実行されないことを確認
            mock_run.assert_not_called()

    def test_clone_with_github_token(self, tmp_path: Path) -> None:
        """GitHub Tokenが指定されている場合、認証URLが使用されることを確認"""
        token = "ghp_test_token"
        cloner = RepositoryCloner(github_token=token)
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            cloner.clone(repo_url, destination)

            args = mock_run.call_args[0][0]
            # トークンが埋め込まれたURLが使用されることを確認
            assert args[3] == f"https://{token}@github.com/test/repo.git"

    def test_clone_failure(self, tmp_path: Path) -> None:
        """クローンに失敗した場合にCalledProcessErrorが発生することを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=128,
                cmd=["git", "clone"],
                stderr="fatal: repository not found",
            )

            with pytest.raises(subprocess.CalledProcessError):
                cloner.clone(repo_url, destination)

    def test_clone_timeout(self, tmp_path: Path) -> None:
        """タイムアウトした場合にTimeoutExpiredが発生することを確認"""
        cloner = RepositoryCloner()
        repo_url = "https://github.com/test/repo.git"
        destination = tmp_path / "test-repo"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["git", "clone"],
                timeout=600,
            )

            with pytest.raises(subprocess.TimeoutExpired):
                cloner.clone(repo_url, destination, timeout=600)
