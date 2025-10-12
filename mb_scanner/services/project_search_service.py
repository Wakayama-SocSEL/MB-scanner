"""プロジェクト検索に関するビジネスロジックを提供するサービス層

このモジュールでは、Projectの検索・フィルタリング機能を担当します。
複雑なクエリやJOINを使った検索ロジックを集約します。
"""

from sqlalchemy.orm import Session

from mb_scanner.models.project import Project, Topic


class ProjectSearchService:
    """プロジェクト検索を提供するサービスクラス

    単一責任の原則に基づき、検索・フィルタリング機能のみを担当します。
    """

    def __init__(self, db: Session) -> None:
        """ProjectSearchServiceを初期化する

        Args:
            db: SQLAlchemyのセッションオブジェクト
        """
        self.db = db

    def search_by_topic(self, topic_name: str) -> list[Project]:
        """指定されたtopicを持つプロジェクトを検索する

        Args:
            topic_name: 検索するtopic名

        Returns:
            list[Project]: 該当するプロジェクトのリスト
        """
        return self.db.query(Project).join(Project.topics).filter(Topic.name == topic_name).all()

    def search_by_language(self, language: str) -> list[Project]:
        """指定された言語のプロジェクトを取得する

        Args:
            language: プログラミング言語名

        Returns:
            list[Project]: 該当するプロジェクトのリスト
        """
        return self.db.query(Project).filter(Project.language == language).all()

    def search_by_min_stars(self, min_stars: int) -> list[Project]:
        """指定されたスター数以上のプロジェクトを取得する

        Args:
            min_stars: 最小スター数

        Returns:
            list[Project]: 該当するプロジェクトのリスト
        """
        return self.db.query(Project).filter(Project.stars >= min_stars).all()
