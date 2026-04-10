"""ベンチマークデータのPydanticモデル

このモジュールは、MicroBench由来のベンチマークJSONLファイルを
読み込むためのモデルを定義します。
"""

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer


class StrategyResult(BaseModel):
    """個別戦略の比較結果

    Attributes:
        comparison_method: 使用した比較戦略
        status: この戦略での比較結果
        slow_output: slow版の実行出力
        fast_output: fast版の実行出力
        error_message: エラーメッセージ（エラー時のみ）
    """

    comparison_method: Literal["stdout", "functions", "variables"]
    """使用した比較戦略"""

    status: Literal["equal", "not_equal", "error"]
    """この戦略での比較結果"""

    slow_output: list[Any] | dict[str, Any] | str | None = None
    """slow版の実行出力"""

    fast_output: list[Any] | dict[str, Any] | str | None = None
    """fast版の実行出力"""

    error_message: str | None = None
    """エラーメッセージ（エラー時のみ）"""

    @field_serializer("slow_output", "fast_output")
    def format_output(self, value: list[Any] | dict[str, Any] | str | None) -> list[Any] | dict[str, Any] | str | None:
        """JSON文字列の場合、JSONオブジェクトに変換して見やすくする"""
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value


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
        strategy_results: not_equal / error となった戦略の結果リスト
        error_message: エラーが発生した場合のメッセージ
    """

    id: int
    """ベンチマークエントリの一意識別子"""

    status: Literal["equal", "not_equal", "error", "timeout", "skipped"]
    """チェック結果のステータス"""

    strategy_results: list[StrategyResult] = []
    """not_equal / error となった戦略の結果リスト（equal は stderr にのみ出力される）"""

    error_message: str | None = None
    """エラーが発生した場合のメッセージ"""


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
