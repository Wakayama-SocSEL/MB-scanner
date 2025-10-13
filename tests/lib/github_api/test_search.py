"""SearchCriteria と検索クエリビルダーのテスト"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mb_scanner.lib.github import search as search_module
from mb_scanner.lib.github.search import SearchCriteria, build_default_search_criteria


def test_search_criteria_model_creation():
    """SearchCriteriaモデルが正しく作成できることを確認する"""
    # Arrange & Act
    criteria = SearchCriteria(
        language="JavaScript",
        min_stars=100,
        max_days_since_commit=365,
    )

    # Assert
    assert criteria.language == "JavaScript"
    assert criteria.min_stars == 100
    assert criteria.max_days_since_commit == 365


def test_search_criteria_to_query_string():
    """SearchCriteriaが正しいGitHub検索クエリ文字列を生成することを確認する"""
    # Arrange
    criteria = SearchCriteria(
        language="JavaScript",
        min_stars=100,
        max_days_since_commit=365,
    )

    # Act
    query = criteria.to_query_string()

    # Assert
    assert "language:javascript" in query
    assert "stars:>=100" in query
    assert "pushed:>" in query

    # 日付部分を確認（正確な日付は現在日時に依存するため、形式のみチェック）
    cutoff_date = datetime.now(UTC) - timedelta(days=365)
    expected_date_str = cutoff_date.strftime("%Y-%m-%d")
    assert expected_date_str in query


def test_search_criteria_to_query_string_different_language():
    """異なる言語でもクエリが正しく生成されることを確認する"""
    # Arrange
    criteria = SearchCriteria(
        language="Python",
        min_stars=500,
        max_days_since_commit=180,
    )

    # Act
    query = criteria.to_query_string()

    # Assert
    assert "language:python" in query  # 小文字に変換される
    assert "stars:>=500" in query

    cutoff_date = datetime.now(UTC) - timedelta(days=180)
    expected_date_str = cutoff_date.strftime("%Y-%m-%d")
    assert expected_date_str in query


def test_search_criteria_min_stars_validation():
    """min_starsが負の値の場合にバリデーションエラーが発生することを確認する"""
    # Act & Assert
    with pytest.raises(ValueError):  # Pydantic ValidationError
        SearchCriteria(
            language="JavaScript",
            min_stars=-1,  # 負の値
            max_days_since_commit=365,
        )


def test_search_criteria_max_days_since_commit_validation():
    """max_days_since_commitが0以下の場合にバリデーションエラーが発生することを確認する"""
    # Act & Assert
    with pytest.raises(ValueError):  # Pydantic ValidationError
        SearchCriteria(
            language="JavaScript",
            min_stars=100,
            max_days_since_commit=0,  # 0以下
        )


def test_build_default_search_criteria():
    """デフォルトの検索条件が正しく生成されることを確認する"""
    # Arrange
    fake_settings = SimpleNamespace(
        github_search_default_language="JavaScript",
        github_search_default_min_stars=100,
        github_search_default_max_days_since_commit=365,
    )

    # Act
    with patch.object(search_module, "settings", fake_settings):
        criteria = build_default_search_criteria()

    # Assert
    assert criteria.language == "JavaScript"
    assert criteria.min_stars == 100
    assert criteria.max_days_since_commit == 365


def test_build_default_search_criteria_query_string():
    """デフォルトの検索条件から生成されるクエリ文字列が正しいことを確認する"""
    # Arrange
    fake_settings = SimpleNamespace(
        github_search_default_language="JavaScript",
        github_search_default_min_stars=100,
        github_search_default_max_days_since_commit=365,
    )

    # Act
    with patch.object(search_module, "settings", fake_settings):
        criteria = build_default_search_criteria()
        query = criteria.to_query_string()

    # Assert
    assert "language:javascript" in query
    assert "stars:>=100" in query
    assert "pushed:>" in query
