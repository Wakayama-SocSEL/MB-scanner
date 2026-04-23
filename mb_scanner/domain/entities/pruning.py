"""Pruning (Hydra 式 AST 差分フィルタ) の入出力 Pydantic モデル

Node.js 側 (`mb-analyzer/src/shared/types.ts`) と JSON シリアライゼーション互換を保つ。
フィールド名は snake_case、列挙値文字列も両言語で完全一致。

- ``PruningInput`` は外部入力 (CLI/JSONL) のため ``extra="forbid"`` で典型ミスを弾く
- ``PruningResult`` は Node 側の将来フィールド追加に備えて ``extra="ignore"``
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, JsonValue

MAX_CODE_LENGTH = 1_000_000
MIN_TIMEOUT_MS = 1
MAX_TIMEOUT_MS = 60_000
DEFAULT_TIMEOUT_MS = 5_000
DEFAULT_MAX_ITERATIONS = 1_000
MIN_MAX_ITERATIONS = 1


class PruningVerdict(StrEnum):
    """pruning 全体判定"""

    PRUNED = "pruned"
    INITIAL_MISMATCH = "initial_mismatch"
    ERROR = "error"


class PlaceholderKind(StrEnum):
    """置換後のワイルドカード種別"""

    EXPRESSION = "expression"
    STATEMENT = "statement"
    IDENTIFIER = "identifier"


class Placeholder(BaseModel):
    """pruning の結果 AST に差し込まれるワイルドカード

    ``original_snippet`` は置換前の slow コード片をそのまま保持し、第 2 段階で参照する。
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    kind: PlaceholderKind
    original_snippet: str


class PruningInput(BaseModel):
    """Node ランナーへ送る pruning 入力

    ``setup`` は単数 (複数 setup は第 2 段階の軸に委ねる設計)。
    ``id`` はバッチ API で Python ↔ Node 間の順序暗黙依存を避ける optional マーカー。
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    slow: str = Field(max_length=MAX_CODE_LENGTH)
    fast: str = Field(max_length=MAX_CODE_LENGTH)
    setup: str = Field(default="", max_length=MAX_CODE_LENGTH)
    timeout_ms: int = Field(default=DEFAULT_TIMEOUT_MS, ge=MIN_TIMEOUT_MS, le=MAX_TIMEOUT_MS)
    max_iterations: int = Field(default=DEFAULT_MAX_ITERATIONS, ge=MIN_MAX_ITERATIONS)


class PruningResult(BaseModel):
    """1 (slow, fast, setup) トリプルに対する pruning 最終結果

    - ``verdict == PRUNED``: ``pattern_ast`` / ``pattern_code`` / ``placeholders`` が揃う
    - ``verdict == INITIAL_MISMATCH``: slow ≢ fast のため pruning 前段で停止
    - ``verdict == ERROR``: parse 失敗やタイムアウトなど予期しない失敗
    """

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    verdict: PruningVerdict
    pattern_ast: JsonValue = None
    pattern_code: str | None = None
    placeholders: list[Placeholder] = Field(default_factory=list[Placeholder])
    iterations: int | None = None
    node_count_before: int | None = None
    node_count_after: int | None = None
    effective_timeout_ms: int | None = None
    error_message: str | None = None
