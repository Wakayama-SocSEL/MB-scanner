"""Topicに関するビジネスロジックを提供するサービス層

このモジュールでは、Topicテーブルの操作を担当します。
"""

from sqlalchemy.orm import Session

from mb_scanner.models.project import Topic


class TopicService:
    """Topicテーブルの操作を提供するサービスクラス

    単一責任の原則に基づき、Topicテーブルの操作のみを担当します。
    """

    def __init__(self, db: Session) -> None:
        """TopicServiceを初期化する

        Args:
            db: SQLAlchemyのセッションオブジェクト
        """
        self.db = db

    def get_topic_by_name(self, name: str) -> Topic | None:
        """名前でtopicを取得する

        Args:
            name: topic名

        Returns:
            Topic: 見つかった場合はTopicオブジェクト、見つからない場合はNone
        """
        return self.db.query(Topic).filter(Topic.name == name).first()

    def get_all_topics(self) -> list[Topic]:
        """全てのtopicを取得する

        Returns:
            list[Topic]: topicのリスト
        """
        return self.db.query(Topic).all()

    def count_topics(self) -> int:
        """topicの総数を取得する

        Returns:
            int: topicの総数
        """
        return self.db.query(Topic).count()

    def get_or_create_topics(self, topic_names: list[str]) -> list[Topic]:
        """topic名のリストから、Topicオブジェクトのリストを取得または作成する

        既に存在するtopicは取得し、存在しないtopicは新規作成します。
        このメソッドは、Projectとtopicを関連付ける際に使用されます。

        Args:
            topic_names: topic名のリスト

        Returns:
            list[Topic]: Topicオブジェクトのリスト
        """
        topics: list[Topic] = []
        for name in topic_names:
            # 既存のtopicを検索
            topic = self.get_topic_by_name(name)
            if not topic:
                # 存在しなければ新規作成
                topic = Topic(name=name)
                self.db.add(topic)
            topics.append(topic)

        # まとめてコミット（効率化）
        self.db.flush()
        return topics
