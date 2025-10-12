"""データベースセッション管理モジュール

このモジュールでは、SQLAlchemyのエンジンとセッションを管理します。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mb_scanner.core.config import settings
from mb_scanner.db.base import Base

# データベースエンジンの作成
# check_same_thread=False: SQLiteでマルチスレッドを許可（開発用）
# echo=False: SQLのログ出力を無効化（必要に応じてTrueに変更可能）
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session]:
    """データベースセッションを取得するジェネレータ

    依存性注入（Dependency Injection）パターンで使用します。
    セッションを自動的に閉じるため、with文やジェネレータとして使用します。

    Yields:
        Session: SQLAlchemyのセッションオブジェクト

    Examples:
        >>> with next(get_db()) as db:
        ...     repositories = db.query(Repository).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """データベースを初期化し、全てのテーブルを作成する

    この関数は、アプリケーションの起動時に一度だけ呼び出されます。
    既に存在するテーブルは再作成されません。

    Examples:
        >>> init_db()  # 全てのテーブルが作成される
    """
    # 全てのモデルをインポートして、Base.metadataに登録する必要があります
    from mb_scanner.models import project  # noqa: F401, PLC0415

    # テーブル作成
    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """全てのテーブルを削除する

    警告: この関数はデータベース内の全データを削除します。
    テスト環境でのみ使用してください。

    Examples:
        >>> drop_all_tables()  # 全てのテーブルが削除される
    """
    Base.metadata.drop_all(bind=engine)
