"""GitHubRepository Pydanticモデルのテスト"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from mb_scanner.lib.github.schema import GitHubRepository


def test_github_repository_model_creation():
    """GitHubRepositoryモデルが正しく作成できることを確認する"""
    # Arrange
    repo_data = {
        "full_name": "facebook/react",
        "html_url": "https://github.com/facebook/react",
        "stargazers_count": 50000,
        "pushed_at": datetime(2024, 1, 1, tzinfo=UTC),
        "language": "JavaScript",
        "description": "A declarative, efficient, and flexible JavaScript library",
        "topics": ["react", "javascript", "ui"],
    }

    # Act
    repo = GitHubRepository(**repo_data)

    # Assert
    assert repo.full_name == "facebook/react"
    assert repo.html_url == "https://github.com/facebook/react"
    assert repo.stargazers_count == 50000
    assert repo.pushed_at == datetime(2024, 1, 1, tzinfo=UTC)
    assert repo.language == "JavaScript"
    assert repo.description == "A declarative, efficient, and flexible JavaScript library"
    assert repo.topics == ["react", "javascript", "ui"]


def test_github_repository_model_with_optional_fields():
    """GitHubRepositoryモデルがオプショナルフィールドを正しく扱うことを確認する"""
    # Arrange
    repo_data = {
        "full_name": "example/repo",
        "html_url": "https://github.com/example/repo",
        "stargazers_count": 0,
    }

    # Act
    repo = GitHubRepository(**repo_data)

    # Assert
    assert repo.full_name == "example/repo"
    assert repo.html_url == "https://github.com/example/repo"
    assert repo.stargazers_count == 0
    assert repo.pushed_at is None
    assert repo.language is None
    assert repo.description is None
    assert repo.topics == []


def test_github_repository_from_pygithub():
    """PyGithubのRepositoryオブジェクトからGitHubRepositoryを作成できることを確認する"""
    # Arrange: PyGithubのRepositoryオブジェクトをモック
    mock_repo = Mock()
    mock_repo.full_name = "facebook/react"
    mock_repo.html_url = "https://github.com/facebook/react"
    mock_repo.stargazers_count = 50000
    mock_repo.pushed_at = datetime(2024, 1, 1, tzinfo=UTC)
    mock_repo.language = "JavaScript"
    mock_repo.description = "A declarative, efficient, and flexible JavaScript library"
    mock_repo.get_topics.return_value = ["react", "javascript", "ui"]

    # Act
    repo = GitHubRepository.from_pygithub(mock_repo)

    # Assert
    assert repo.full_name == "facebook/react"
    assert repo.html_url == "https://github.com/facebook/react"
    assert repo.stargazers_count == 50000
    assert repo.pushed_at == datetime(2024, 1, 1, tzinfo=UTC)
    assert repo.language == "JavaScript"
    assert repo.description == "A declarative, efficient, and flexible JavaScript library"
    assert repo.topics == ["react", "javascript", "ui"]
    mock_repo.get_topics.assert_called_once()


def test_github_repository_stargazers_count_validation():
    """stargazers_countが負の値の場合にバリデーションエラーが発生することを確認する"""
    # Arrange
    repo_data = {
        "full_name": "example/repo",
        "html_url": "https://github.com/example/repo",
        "stargazers_count": -1,  # 負の値
    }

    # Act & Assert
    with pytest.raises(ValueError):  # Pydantic ValidationError
        GitHubRepository(**repo_data)
