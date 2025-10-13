"""GitHubClient のテスト"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from mb_scanner.lib.github.client import GitHubClient
from mb_scanner.lib.github.search import SearchCriteria


def test_github_client_initialization_with_token():
    """GitHubClientがトークン付きで正しく初期化されることを確認する"""
    # Arrange & Act
    with patch("mb_scanner.lib.github.client.Github"):
        client = GitHubClient(token="test_token")

    # Assert
    assert client.token == "test_token"


def test_github_client_initialization_without_token():
    """GitHubClientがトークンなしで初期化時にエラーを発生させることを確認する"""
    # Arrange & Act & Assert
    with patch("mb_scanner.lib.github.client.settings") as mock_settings:
        mock_settings.github_token = None
        with pytest.raises(ValueError, match="GitHub token is not configured"):
            GitHubClient()


def test_github_client_search_repositories():
    """GitHubClientが検索を正しく実行できることを確認する"""
    # Arrange: モックリポジトリを作成
    mock_repo1 = Mock()
    mock_repo1.full_name = "facebook/react"
    mock_repo1.html_url = "https://github.com/facebook/react"
    mock_repo1.stargazers_count = 50000
    mock_repo1.pushed_at = datetime(2024, 1, 1, tzinfo=UTC)
    mock_repo1.language = "JavaScript"
    mock_repo1.description = "A declarative JavaScript library"
    mock_repo1.get_topics.return_value = ["react", "javascript"]

    mock_repo2 = Mock()
    mock_repo2.full_name = "vuejs/vue"
    mock_repo2.html_url = "https://github.com/vuejs/vue"
    mock_repo2.stargazers_count = 40000
    mock_repo2.pushed_at = datetime(2024, 2, 1, tzinfo=UTC)
    mock_repo2.language = "JavaScript"
    mock_repo2.description = "Progressive JavaScript framework"
    mock_repo2.get_topics.return_value = ["vue", "javascript"]

    # GitHubClientをモック
    with (
        patch("mb_scanner.lib.github.client.Github") as mock_github_class,
        patch("mb_scanner.lib.github.client.cast") as mock_cast,
    ):
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.return_value = [mock_repo1, mock_repo2]

        # castはそのまま渡すように設定
        mock_cast.side_effect = lambda _, x: x

        client = GitHubClient(token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        results = client.search_repositories(criteria, max_results=10)

    # Assert
    assert len(results) == 2
    assert results[0].full_name == "facebook/react"
    assert results[1].full_name == "vuejs/vue"
    mock_github_instance.search_repositories.assert_called_once()


def test_github_client_search_repositories_with_max_results():
    """GitHubClientが最大結果数を正しく制限することを確認する"""
    # Arrange: 多数のモックリポジトリを作成
    mock_repos = []
    for i in range(200):
        mock_repo = Mock()
        mock_repo.full_name = f"user/repo{i}"
        mock_repo.html_url = f"https://github.com/user/repo{i}"
        mock_repo.stargazers_count = 100
        mock_repo.pushed_at = datetime(2024, 1, 1, tzinfo=UTC)
        mock_repo.language = "JavaScript"
        mock_repo.description = "Test repo"
        mock_repo.get_topics.return_value = []
        mock_repos.append(mock_repo)

    with (
        patch("mb_scanner.lib.github.client.Github") as mock_github_class,
        patch("mb_scanner.lib.github.client.cast") as mock_cast,
    ):
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.return_value = mock_repos

        # castはそのまま渡すように設定
        mock_cast.side_effect = lambda _, x: x

        client = GitHubClient(token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        results = client.search_repositories(criteria, max_results=50)

    # Assert
    assert len(results) == 50  # max_resultsで制限される


def test_github_client_search_repositories_github_exception():
    """GitHubClientがGitHub APIエラーを正しく処理することを確認する"""
    # Arrange
    with patch("mb_scanner.lib.github.client.Github") as mock_github_class:
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance

        # RuntimeErrorを発生させる
        test_exception = RuntimeError("API Error")
        mock_github_instance.search_repositories.side_effect = test_exception

        client = GitHubClient(token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act & Assert
        with pytest.raises(RuntimeError, match="API Error"):
            client.search_repositories(criteria)


def test_github_client_get_rate_limit_info():
    """GitHubClientがレート制限情報を正しく取得できることを確認する"""
    # Arrange
    with patch("mb_scanner.lib.github.client.Github") as mock_github_class:
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance

        # レート制限情報をモック (overview.resources.core 構造)
        mock_overview = Mock()
        mock_resources = Mock()
        mock_core_limit = Mock()
        mock_core_limit.limit = 5000
        mock_core_limit.remaining = 4500
        mock_core_limit.reset = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_resources.core = mock_core_limit
        mock_overview.resources = mock_resources
        mock_github_instance.get_rate_limit.return_value = mock_overview

        client = GitHubClient(token="test_token")

        # Act
        rate_info = client.get_rate_limit_info()

    # Assert
    assert rate_info["limit"] == 5000
    assert rate_info["remaining"] == 4500
    assert "reset_time" in rate_info
    assert "wait_seconds" in rate_info
    assert rate_info["reset_time"] == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    # remaining > 0 なので wait_seconds は 0
    assert rate_info["wait_seconds"] == 0.0


def test_github_client_close():
    """GitHubClientが正しくクローズできることを確認する"""
    # Arrange
    with patch("mb_scanner.lib.github.client.Github") as mock_github_class:
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance

        client = GitHubClient(token="test_token")

        # Act
        client.close()

    # Assert
    mock_github_instance.close.assert_called_once()


def test_github_client_search_repositories_with_default_criteria():
    """GitHubClientがデフォルト検索条件で正しく検索できることを確認する"""
    # Arrange: モックリポジトリを作成
    mock_repo = Mock()
    mock_repo.full_name = "user/repo"
    mock_repo.html_url = "https://github.com/user/repo"
    mock_repo.stargazers_count = 100
    mock_repo.pushed_at = datetime(2024, 1, 1, tzinfo=UTC)
    mock_repo.language = "Python"
    mock_repo.description = "Test repo"
    mock_repo.get_topics.return_value = ["python"]

    with (
        patch("mb_scanner.lib.github.client.Github") as mock_github_class,
        patch("mb_scanner.lib.github.client.cast") as mock_cast,
        patch("mb_scanner.lib.github.client.build_default_search_criteria") as mock_build_default,
    ):
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_github_instance.search_repositories.return_value = [mock_repo]

        # castはそのまま渡すように設定
        mock_cast.side_effect = lambda _, x: x

        # デフォルト検索条件を設定
        default_criteria = SearchCriteria(
            language="Python",
            min_stars=100,
            max_days_since_commit=365,
        )
        mock_build_default.return_value = default_criteria

        client = GitHubClient(token="test_token")

        # Act: criteriaを指定せずに呼び出す
        results = client.search_repositories(max_results=10)

    # Assert
    assert len(results) == 1
    assert results[0].full_name == "user/repo"
    # build_default_search_criteriaが呼ばれたことを確認
    mock_build_default.assert_called_once()
    # デフォルト条件のクエリが使われたことを確認
    expected_query = default_criteria.to_query_string()
    mock_github_instance.search_repositories.assert_called_once_with(query=expected_query)
