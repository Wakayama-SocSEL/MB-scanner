"""pytest 共通フィクスチャ

このモジュールでは、全テストで共有されるフィクスチャを定義します。
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mb_scanner.db.base import Base
from mb_scanner.services.project_search_service import ProjectSearchService
from mb_scanner.services.project_service import ProjectService
from mb_scanner.services.topic_service import TopicService


@pytest.fixture(scope="function")
def test_db() -> Generator[Session]:
    """テスト用のインメモリDBセッションを提供するフィクスチャ

    各テスト関数ごとに新しいDBインスタンスを作成し、テスト終了後にクリーンアップします。
    scope="function" により、各テストが独立した環境で実行されます。

    Yields:
        Session: テスト用のSQLAlchemyセッション
    """
    # インメモリSQLiteエンジンを作成
    engine = create_engine("sqlite:///:memory:", echo=False)

    # テーブルを作成
    Base.metadata.create_all(bind=engine)

    # セッションファクトリを作成
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # セッションを作成して提供
    db = test_session_local()

    try:
        yield db
    finally:
        db.close()
        # テーブルを削除（クリーンアップ）
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def topic_service(test_db: Session) -> TopicService:
    """TopicService のインスタンスを提供するフィクスチャ

    Args:
        test_db: テスト用DBセッション

    Returns:
        TopicService: テスト用サービスインスタンス
    """
    return TopicService(test_db)


@pytest.fixture
def project_service(test_db: Session) -> ProjectService:
    """ProjectService のインスタンスを提供するフィクスチャ

    Args:
        test_db: テスト用DBセッション

    Returns:
        ProjectService: テスト用サービスインスタンス
    """
    return ProjectService(test_db)


@pytest.fixture
def search_service(test_db: Session) -> ProjectSearchService:
    """ProjectSearchService のインスタンスを提供するフィクスチャ

    Args:
        test_db: テスト用DBセッション

    Returns:
        ProjectSearchService: テスト用サービスインスタンス
    """
    return ProjectSearchService(test_db)
