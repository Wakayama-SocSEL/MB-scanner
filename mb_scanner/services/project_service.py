"""プロジェクトに関するビジネスロジックを提供するサービス層

このモジュールでは、Projectテーブルの基本的なCRUD操作を担当します。
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from mb_scanner.models.project import Project
from mb_scanner.services.topic_service import TopicService


class ProjectService:
    """Projectテーブルの基本操作を提供するサービスクラス

    単一責任の原則に基づき、Projectテーブルの基本CRUD操作のみを担当します。
    Topic関連の操作はTopicServiceに委譲します。
    """

    def __init__(self, db: Session) -> None:
        """ProjectServiceを初期化する

        Args:
            db: SQLAlchemyのセッションオブジェクト
        """
        self.db = db
        self.topic_service = TopicService(db)

    def get_project_by_full_name(self, full_name: str) -> Project | None:
        """full_nameでプロジェクトを検索する

        Args:
            full_name: プロジェクト名（owner/repo形式）

        Returns:
            Project: 見つかった場合はProjectオブジェクト、見つからない場合はNone
        """
        return self.db.query(Project).filter(Project.full_name == full_name).first()

    def get_all_projects(self) -> list[Project]:
        """全てのプロジェクトを取得する

        Returns:
            list[Project]: プロジェクトのリスト
        """
        return self.db.query(Project).all()

    def count_projects(self) -> int:
        """プロジェクトの総数を取得する

        Returns:
            int: プロジェクトの総数
        """
        return self.db.query(Project).count()

    def get_all_project_urls(self) -> list[tuple[int, str, str]]:
        """全プロジェクトの(id, full_name, url)を取得する

        Returns:
            list[tuple[int, str, str]]: [(project_id, full_name, url), ...]
        """
        projects = self.db.query(Project.id, Project.full_name, Project.url).all()
        return [(p.id, p.full_name, p.url) for p in projects]

    def save_project(
        self,
        full_name: str,
        url: str,
        stars: int,
        language: str | None,
        description: str | None,
        last_commit_date: datetime | None,
        topics: list[str] | None = None,
        *,
        update_if_exists: bool = False,
    ) -> Project:
        """プロジェクトを保存する

        既に同じfull_nameのプロジェクトが存在する場合、update_if_existsがTrueなら更新、
        Falseなら既存のプロジェクトをそのまま返します。

        Args:
            full_name: プロジェクト名（owner/repo形式）
            url: GitHub Web URL
            stars: スター数
            language: 主要言語
            description: プロジェクト説明文
            last_commit_date: 最終コミット日時
            topics: topicのリスト
            update_if_exists: 既存プロジェクトを更新するか（デフォルト: False）

        Returns:
            Project: 保存されたプロジェクトオブジェクト
        """
        # 既存のプロジェクトをチェック
        existing_project = self.get_project_by_full_name(full_name)

        if existing_project:
            if update_if_exists:
                # 既存プロジェクトを更新
                existing_project.url = url
                existing_project.stars = stars
                existing_project.language = language
                existing_project.description = description
                existing_project.last_commit_date = last_commit_date
                existing_project.fetched_at = datetime.now(UTC)

                # topicsの更新（TopicServiceに委譲）
                if topics:
                    existing_project.topics = self.topic_service.get_or_create_topics(topics)

                self.db.commit()
                self.db.refresh(existing_project)
                return existing_project
            # update_if_existsがFalseなら既存のものを返す
            return existing_project

        # 新規プロジェクトを作成
        new_project = Project(
            full_name=full_name,
            url=url,
            stars=stars,
            language=language,
            description=description,
            last_commit_date=last_commit_date,
            fetched_at=datetime.now(UTC),
        )

        # topicsの関連付け（TopicServiceに委譲）
        if topics:
            new_project.topics = self.topic_service.get_or_create_topics(topics)

        self.db.add(new_project)
        self.db.commit()
        self.db.refresh(new_project)
        return new_project
