"""ベンチマークデータのPydanticモデル

このモジュールは、MicroBench由来のベンチマークJSONLファイルを
読み込むためのモデルを定義します。
"""

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer


class BenchmarkEntry(BaseModel):
    """JSONLの各行を表すモデル

    Attributes:
        id: ベンチマークエントリの一意識別子
        slow: 遅いバージョンのJavaScriptコード
        fast: 速いバージョンのJavaScriptコード
        slow_fast_medi_time: slow版とfast版の実行時間の差（中央値）
    """

    id: int
    """ベンチマークエントリの一意識別子"""

    slow: str
    """遅いバージョンのJavaScriptコード"""

    fast: str
    """速いバージョンのJavaScriptコード"""

    slow_fast_medi_time: float | str = Field(validation_alias="slow-fast_mediTime")
    """slow版とfast版の実行時間の差（中央値）。エラーの場合は文字列"""


class EquivalenceResult(BaseModel):
    """slow/fastコードの等価性チェック結果

    Attributes:
        id: ベンチマークエントリの一意識別子
        status: チェック結果のステータス
        slow_output: slow版の実行出力（JSONオブジェクトまたは文字列）
        fast_output: fast版の実行出力（JSONオブジェクトまたは文字列）
        comparison_method: 比較に使用した方法
        error_message: エラーが発生した場合のメッセージ
    """

    id: int
    """ベンチマークエントリの一意識別子"""

    status: Literal["equal", "not_equal", "error", "timeout", "skipped"]
    """チェック結果のステータス"""

    slow_output: dict[str, Any] | str | None = None
    """slow版の実行出力（JSONオブジェクトまたは文字列）"""

    fast_output: dict[str, Any] | str | None = None
    """fast版の実行出力（JSONオブジェクトまたは文字列）"""

    comparison_method: Literal["stdout", "functions", "variables", "none"]
    """比較に使用した方法"""

    error_message: str | None = None
    """エラーが発生した場合のメッセージ"""

    @field_serializer("slow_output", "fast_output")
    def format_output(self, value: dict[str, Any] | str | None) -> dict[str, Any] | str | None:
        """JSON文字列の場合、JSONオブジェクトに変換して見やすくする

        Args:
            value: 出力（JSON文字列、JSONオブジェクト、プレーンテキスト、またはNone）

        Returns:
            JSON文字列の場合はパースしたJSONオブジェクト、
            既にJSONオブジェクトの場合はそのまま、
            プレーンテキストの場合は元の文字列、
            Noneの場合はNone
        """
        if value is None:
            return None

        # 既にdictオブジェクトの場合はそのまま返す
        if isinstance(value, dict):
            return value

        # 文字列の場合、JSONパースを試みる
        if isinstance(value, str):
            try:
                # JSON文字列をパースしてオブジェクトに変換
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # パースに失敗した場合は元の文字列を返す（プレーンテキスト）
                return value

        return value


class EquivalenceSummary(BaseModel):
    """等価性チェックの全体サマリー

    Attributes:
        total: 全チェック件数
        equal: 等価と判定された件数
        not_equal: 非等価と判定された件数
        error: エラーが発生した件数
        timeout: タイムアウトした件数
        skipped: スキップされた件数
        results: 個別の結果リスト
    """

    total: int
    """全チェック件数"""

    equal: int
    """等価と判定された件数"""

    not_equal: int
    """非等価と判定された件数"""

    error: int
    """エラーが発生した件数"""

    timeout: int
    """タイムアウトした件数"""

    skipped: int
    """スキップされた件数"""

    results: list[EquivalenceResult]
    """個別の結果リスト"""
