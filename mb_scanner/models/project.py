"""GitHubプロジェクト関連のデータモデル

このモジュールでは、以下の3つのテーブルを定義します：
- Project: プロジェクトの基本情報
- Topic: GitHubのtopicマスタ
- ProjectTopic: プロジェクトとtopicの多対多関係（中間テーブル）
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mb_scanner.db.base import Base

if TYPE_CHECKING:
    pass


class Project(Base):
    """GitHubプロジェクトを表すモデル

    Attributes:
        id: 内部ID（主キー）
        full_name: プロジェクト名（owner/repo形式）
        url: GitHub Web URL
        stars: スター数
        last_commit_date: 最終コミット日時（pushed_at）
        language: 主要言語
        description: プロジェクト説明文
        fetched_at: データ取得日時
        js_lines_count: JavaScriptファイルの総行数
        topics: 関連するTopicのリスト（リレーションシップ）
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    last_commit_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    js_lines_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # リレーションシップ: 多対多（Project ↔ Topic）
    topics: Mapped[list["Topic"]] = relationship(
        "Topic", secondary="project_topics", back_populates="projects", lazy="selectin"
    )

    def __repr__(self) -> str:
        """デバッグ用の文字列表現"""
        return f"<Project(id={self.id}, full_name='{self.full_name}', stars={self.stars}, language='{self.language}')>"


class Topic(Base):
    """GitHubのtopicを表すモデル

    Attributes:
        id: 内部ID（主キー）
        name: topic名
        projects: このtopicを持つProjectのリスト（リレーションシップ）
    """

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # リレーションシップ: 多対多（Topic ↔ Project）
    projects: Mapped[list["Project"]] = relationship(
        "Project", secondary="project_topics", back_populates="topics", lazy="selectin"
    )

    def __repr__(self) -> str:
        """デバッグ用の文字列表現"""
        return f"<Topic(id={self.id}, name='{self.name}')>"


class ProjectTopic(Base):
    """プロジェクトとtopicの多対多関係を表す中間テーブル

    Attributes:
        project_id: プロジェクトID（外部キー）
        topic_id: topicID（外部キー）
    """

    __tablename__ = "project_topics"

    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)

    def __repr__(self) -> str:
        """デバッグ用の文字列表現"""
        return f"<ProjectTopic(project_id={self.project_id}, topic_id={self.topic_id})>"
