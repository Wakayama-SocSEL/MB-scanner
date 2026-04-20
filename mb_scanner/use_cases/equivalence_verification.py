"""等価性検証の Use Case 層

1 トリプル (setup, slow, fast) に対して ``EquivalenceCheckerPort`` を呼び出し、
Port から受け取った observation を使って全体 verdict を導出する。

Pruning や同値分割テストといった複数 setup の処理は呼び出し側の責務。
"""

from collections.abc import Sequence

from mb_scanner.domain.entities.equivalence import (
    EquivalenceCheckResult,
    EquivalenceInput,
    OracleObservation,
    OracleVerdict,
    Verdict,
)
from mb_scanner.domain.ports.equivalence_checker import EquivalenceCheckerPort


def derive_overall_verdict(observations: list[OracleObservation]) -> Verdict:
    """Oracle observation から全体 verdict を導く純粋関数

    優先順位:
        1. not_equal が 1 つでもある → not_equal
        2. error が 1 つでもある → error
        3. 全 oracle が not_applicable → error（観測対象ゼロ）
        4. equal が 1 つでもある → equal
        5. フォールバック → error
    """
    verdicts = [o.verdict for o in observations]
    if OracleVerdict.NOT_EQUAL in verdicts:
        return Verdict.NOT_EQUAL
    if OracleVerdict.ERROR in verdicts:
        return Verdict.ERROR
    if all(v == OracleVerdict.NOT_APPLICABLE for v in verdicts):
        return Verdict.ERROR
    if OracleVerdict.EQUAL in verdicts:
        return Verdict.EQUAL
    return Verdict.ERROR


class EquivalenceVerificationUseCase:
    """等価性検証 Use Case

    Args:
        checker: EquivalenceCheckerPort 実装（通常は NodeRunnerEquivalenceGateway）
    """

    def __init__(self, checker: EquivalenceCheckerPort) -> None:
        self._checker = checker

    def verify(self, input_: EquivalenceInput) -> EquivalenceCheckResult:
        """1 トリプルを検証して結果を返す

        Port から受け取った結果の verdict フィールドは信頼せず、observation から
        ``derive_overall_verdict`` で再計算する。これにより Port 実装側のバグや
        TypeScript / Python の列挙値ズレを use case で検知できる。
        """
        result = self._checker.check(input_)
        return _finalize(result)

    def verify_batch(self, items: Sequence[EquivalenceInput]) -> list[EquivalenceCheckResult]:
        """複数トリプルをまとめて検証して結果リストを返す

        Port の ``check_batch`` を呼び、各結果に ``verify`` と同じ verdict 再計算と
        error 素通し防御を適用する。``id`` は Port が埋めたものを保持する。
        """
        results = self._checker.check_batch(items)
        return [_finalize(result) for result in results]


def _finalize(result: EquivalenceCheckResult) -> EquivalenceCheckResult:
    """Port から受け取った結果を verdict 再計算して確定する共通処理"""
    if result.error_message is not None and not result.observations:
        return result

    recalculated = derive_overall_verdict(result.observations)
    return EquivalenceCheckResult(
        id=result.id,
        verdict=recalculated,
        observations=result.observations,
        error_message=result.error_message,
        effective_timeout_ms=result.effective_timeout_ms,
    )
