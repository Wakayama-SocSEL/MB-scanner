"""GitHub検索機能のモジュール

このモジュールでは、GitHub API検索用のクエリビルダーと
検索条件を表すPydanticモデルを提供します。
"""

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from mb_scanner.core.config import settings


class SearchCriteria(BaseModel):
    """GitHub検索条件を表すPydanticモデル

    Attributes:
        language: 検索対象の主要言語
        min_stars: 最小スター数
        max_days_since_commit: 最終コミットからの最大日数
    """

    language: str = Field(..., description="検索対象の主要言語")
    min_stars: int = Field(..., ge=0, description="最小スター数")
    max_days_since_commit: int = Field(..., ge=1, description="最終コミットからの最大日数")

    def to_query_string(self) -> str:
        """検索条件をGitHub検索クエリ文字列に変換する

        例: "language:javascript stars:>=100 pushed:>2024-01-01"

        Returns:
            str: GitHub API用の検索クエリ文字列
        """
        # 最終コミット日の基準日を計算
        cutoff_date = datetime.now(UTC) - timedelta(days=self.max_days_since_commit)
        date_str = cutoff_date.strftime("%Y-%m-%d")

        # クエリ文字列を構築
        query_parts = [
            f"language:{self.language.lower()}",
            f"stars:>={self.min_stars}",
            f"pushed:>{date_str}",
        ]

        return " ".join(query_parts)


def build_default_search_criteria() -> SearchCriteria:
    """デフォルトの検索条件をconfigから読み込み、作成する

    タスク仕様に基づくデフォルト値：
    - 主要言語
    - スター数
    - 最終コミット

    Returns:
        SearchCriteria: デフォルトの検索条件
    """
    return SearchCriteria(
        language=settings.github_search_default_language,
        min_stars=settings.github_search_default_min_stars,
        max_days_since_commit=settings.github_search_default_max_days_since_commit,
    )
