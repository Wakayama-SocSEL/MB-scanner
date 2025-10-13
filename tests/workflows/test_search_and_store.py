"""SearchAndStoreWorkflow のテスト"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from mb_scanner.lib.github.schema import GitHubRepository
from mb_scanner.lib.github.search import SearchCriteria
from mb_scanner.workflows.search_and_store import SearchAndStoreWorkflow


@pytest.fixture
def mock_github_repositories():
    """テスト用のGitHubRepositoryリストを作成するフィクスチャ"""
    return [
        GitHubRepository(
            full_name="facebook/react",
            html_url="https://github.com/facebook/react",
            stargazers_count=50000,
            pushed_at=datetime(2024, 1, 1, tzinfo=UTC),
            language="JavaScript",
            description="A declarative JavaScript library",
            topics=["react", "javascript"],
        ),
        GitHubRepository(
            full_name="vuejs/vue",
            html_url="https://github.com/vuejs/vue",
            stargazers_count=40000,
            pushed_at=datetime(2024, 2, 1, tzinfo=UTC),
            language="JavaScript",
            description="Progressive JavaScript framework",
            topics=["vue", "javascript"],
        ),
    ]


def test_workflow_initialization(test_db: Session):
    """SearchAndStoreWorkflowが正しく初期化されることを確認する"""
    # Arrange & Act
    with patch("mb_scanner.workflows.search_and_store.GitHubClient"):
        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")

    # Assert
    assert workflow.db == test_db
    assert workflow.github_client is not None
    assert workflow.project_service is not None


def test_workflow_execute_success(test_db: Session, mock_github_repositories):
    """SearchAndStoreWorkflowが正常に実行されることを確認する"""
    # Arrange
    with patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_repositories.return_value = mock_github_repositories

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        stats = workflow.execute(criteria, max_results=10, update_if_exists=False)

    # Assert
    assert stats["total"] == 2
    assert stats["saved"] == 2
    assert stats["updated"] == 0
    assert stats["skipped"] == 0
    assert stats["failed"] == 0

    # GitHubClientのメソッドが呼ばれたことを確認
    mock_client.search_repositories.assert_called_once_with(criteria=criteria, max_results=10)


def test_workflow_execute_with_existing_projects(test_db: Session, mock_github_repositories, project_service):
    """既存プロジェクトがある場合にスキップされることを確認する"""
    # Arrange: 事前に1つのプロジェクトを保存
    project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=40000,
        language="JavaScript",
        description="Old description",
        last_commit_date=datetime(2023, 1, 1, tzinfo=UTC),
        topics=["react"],
    )

    with patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_repositories.return_value = mock_github_repositories

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        stats = workflow.execute(criteria, max_results=10, update_if_exists=False)

    # Assert
    assert stats["total"] == 2
    assert stats["saved"] == 1  # vuejs/vue のみ新規保存
    assert stats["updated"] == 0
    assert stats["skipped"] == 1  # facebook/react はスキップ
    assert stats["failed"] == 0


def test_workflow_execute_with_update(test_db: Session, mock_github_repositories, project_service):
    """update_if_existsがTrueの場合に更新されることを確認する"""
    # Arrange: 事前に1つのプロジェクトを保存
    project_service.save_project(
        full_name="facebook/react",
        url="https://github.com/facebook/react",
        stars=40000,
        language="JavaScript",
        description="Old description",
        last_commit_date=datetime(2023, 1, 1, tzinfo=UTC),
        topics=["react"],
    )

    with patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_repositories.return_value = mock_github_repositories

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        stats = workflow.execute(criteria, max_results=10, update_if_exists=True)

    # Assert
    assert stats["total"] == 2
    assert stats["saved"] == 1  # vuejs/vue のみ新規保存
    assert stats["updated"] == 1  # facebook/react は更新
    assert stats["skipped"] == 0
    assert stats["failed"] == 0

    # 更新されたプロジェクトの内容を確認
    updated_project = project_service.get_project_by_full_name("facebook/react")
    assert updated_project is not None
    assert updated_project.stars == 50000  # 更新されている
    assert updated_project.description == "A declarative JavaScript library"


def test_workflow_execute_with_partial_failure(test_db: Session):
    """一部のリポジトリ保存に失敗した場合の動作を確認する"""
    # Arrange: モックリポジトリを作成（1つは不正なデータ）
    valid_repo = GitHubRepository(
        full_name="facebook/react",
        html_url="https://github.com/facebook/react",
        stargazers_count=50000,
        pushed_at=datetime(2024, 1, 1, tzinfo=UTC),
        language="JavaScript",
        description="A declarative JavaScript library",
        topics=["react"],
    )

    # 不正なリポジトリ（full_nameがNoneなど、保存に失敗するケース）
    invalid_repo = Mock(spec=GitHubRepository)
    invalid_repo.full_name = None  # 不正なデータ

    with patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_repositories.return_value = [valid_repo, invalid_repo]

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")
        criteria = SearchCriteria(language="JavaScript", min_stars=100, max_days_since_commit=365)

        # Act
        stats = workflow.execute(criteria, max_results=10, update_if_exists=False)

    # Assert
    assert stats["total"] == 2
    assert stats["saved"] == 1  # valid_repo のみ保存成功
    assert stats["failed"] == 1  # invalid_repo は失敗


def test_workflow_close(test_db: Session):
    """SearchAndStoreWorkflowが正しくクローズできることを確認する"""
    # Arrange
    with patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")

        # Act
        workflow.close()

    # Assert
    mock_client.close.assert_called_once()


def test_workflow_execute_with_default_criteria(test_db: Session, mock_github_repositories):
    """SearchAndStoreWorkflowがデフォルト検索条件で実行されることを確認する"""
    # Arrange
    with (
        patch("mb_scanner.workflows.search_and_store.GitHubClient") as mock_client_class,
        patch("mb_scanner.workflows.search_and_store.build_default_search_criteria") as mock_build_default,
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.search_repositories.return_value = mock_github_repositories

        # デフォルト検索条件を設定
        default_criteria = SearchCriteria(
            language="Python",
            min_stars=50,
            max_days_since_commit=180,
        )
        mock_build_default.return_value = default_criteria

        workflow = SearchAndStoreWorkflow(db=test_db, github_token="test_token")

        # Act: criteriaを指定せずに呼び出す
        stats = workflow.execute(max_results=10, update_if_exists=False)

    # Assert
    assert stats["total"] == 2
    assert stats["saved"] == 2
    # build_default_search_criteriaが呼ばれたことを確認
    mock_build_default.assert_called_once()
    # デフォルト条件が使われたことを確認
    mock_client.search_repositories.assert_called_once_with(criteria=default_criteria, max_results=10)
