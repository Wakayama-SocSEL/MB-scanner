"""ベンチマークデータのPydanticモデル

このモジュールは、MicroBench由来のベンチマークJSONLファイルを
読み込むためのモデルを定義します。
"""

from pydantic import BaseModel, Field


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
