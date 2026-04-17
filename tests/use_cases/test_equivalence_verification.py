"""等価性検証 Use Case のテスト"""

from collections.abc import Sequence

import pytest

from mb_scanner.domain.entities.equivalence import (
    EquivalenceCheckResult,
    EquivalenceInput,
    Oracle,
    OracleObservation,
    OracleVerdict,
    Verdict,
)
from mb_scanner.use_cases.equivalence_verification import (
    EquivalenceVerificationUseCase,
    derive_overall_verdict,
)


def obs(verdict: OracleVerdict, oracle: Oracle = Oracle.RETURN_VALUE) -> OracleObservation:
    return OracleObservation(oracle=oracle, verdict=verdict)


class TestDeriveOverallVerdict:
    @pytest.mark.parametrize(
        ("verdicts", "expected"),
        [
            # not_equal 優先
            (
                [OracleVerdict.EQUAL, OracleVerdict.NOT_EQUAL, OracleVerdict.NOT_APPLICABLE],
                Verdict.NOT_EQUAL,
            ),
            # error は not_equal の次
            (
                [OracleVerdict.EQUAL, OracleVerdict.ERROR, OracleVerdict.NOT_APPLICABLE],
                Verdict.ERROR,
            ),
            # 全 not_applicable は error
            (
                [OracleVerdict.NOT_APPLICABLE] * 4,
                Verdict.ERROR,
            ),
            # equal が 1 つあれば equal
            (
                [OracleVerdict.EQUAL, OracleVerdict.NOT_APPLICABLE, OracleVerdict.NOT_APPLICABLE],
                Verdict.EQUAL,
            ),
            # 空 observation は error
            ([], Verdict.ERROR),
        ],
    )
    def test_precedence(self, verdicts: Sequence[OracleVerdict], expected: Verdict) -> None:
        observations = [obs(v) for v in verdicts]
        assert derive_overall_verdict(observations) == expected


class _StubChecker:
    """Port スタブ。固定結果を返す"""

    def __init__(self, result: EquivalenceCheckResult) -> None:
        self._result = result
        self.last_input: EquivalenceInput | None = None
        self.last_batch: list[EquivalenceInput] | None = None

    def check(self, input_: EquivalenceInput) -> EquivalenceCheckResult:
        self.last_input = input_
        return self._result

    def check_batch(self, items: Sequence[EquivalenceInput]) -> list[EquivalenceCheckResult]:
        self.last_batch = list(items)
        return [self._result.model_copy(update={"id": item.id}) for item in items]


class TestEquivalenceVerificationUseCase:
    def test_delegates_to_checker(self) -> None:
        expected = EquivalenceCheckResult(
            verdict=Verdict.EQUAL,
            observations=[obs(OracleVerdict.EQUAL)],
        )
        stub = _StubChecker(expected)
        use_case = EquivalenceVerificationUseCase(stub)

        input_ = EquivalenceInput(slow="1", fast="1")
        result = use_case.verify(input_)

        assert stub.last_input == input_
        assert result.verdict is Verdict.EQUAL

    def test_recomputes_overall_verdict(self) -> None:
        """Checker が誤った verdict を返しても use case 側で再計算される"""
        wrong = EquivalenceCheckResult(
            verdict=Verdict.EQUAL,  # 嘘の verdict
            observations=[
                obs(OracleVerdict.NOT_EQUAL),
                obs(OracleVerdict.EQUAL, Oracle.ARGUMENT_MUTATION),
            ],
        )
        use_case = EquivalenceVerificationUseCase(_StubChecker(wrong))
        result = use_case.verify(EquivalenceInput(slow="1", fast="1"))
        assert result.verdict is Verdict.NOT_EQUAL

    def test_passthrough_error_without_observations(self) -> None:
        err = EquivalenceCheckResult(
            verdict=Verdict.ERROR,
            observations=[],
            error_message="node runner crashed",
        )
        use_case = EquivalenceVerificationUseCase(_StubChecker(err))
        result = use_case.verify(EquivalenceInput(slow="1", fast="1"))
        assert result.verdict is Verdict.ERROR
        assert result.error_message == "node runner crashed"


class TestVerifyBatch:
    def test_batch_delegates_to_check_batch(self) -> None:
        expected = EquivalenceCheckResult(
            verdict=Verdict.EQUAL,
            observations=[obs(OracleVerdict.EQUAL)],
        )
        stub = _StubChecker(expected)
        use_case = EquivalenceVerificationUseCase(stub)

        inputs = [
            EquivalenceInput(id="a", slow="1", fast="1"),
            EquivalenceInput(id="b", slow="2", fast="2"),
        ]
        results = use_case.verify_batch(inputs)

        assert stub.last_batch is not None
        assert [i.id for i in stub.last_batch] == ["a", "b"]
        assert [r.id for r in results] == ["a", "b"]
        assert all(r.verdict is Verdict.EQUAL for r in results)

    def test_batch_recomputes_verdict(self) -> None:
        wrong = EquivalenceCheckResult(
            verdict=Verdict.EQUAL,  # 嘘の verdict
            observations=[obs(OracleVerdict.NOT_EQUAL)],
        )
        use_case = EquivalenceVerificationUseCase(_StubChecker(wrong))
        results = use_case.verify_batch([EquivalenceInput(id="a", slow="1", fast="1")])
        assert results[0].verdict is Verdict.NOT_EQUAL

    def test_batch_passthrough_error_without_observations(self) -> None:
        err = EquivalenceCheckResult(
            verdict=Verdict.ERROR,
            observations=[],
            error_message="subprocess crashed",
        )
        use_case = EquivalenceVerificationUseCase(_StubChecker(err))
        results = use_case.verify_batch([EquivalenceInput(id="a", slow="1", fast="1")])
        assert results[0].verdict is Verdict.ERROR
        assert results[0].error_message == "subprocess crashed"

    def test_batch_preserves_effective_timeout_ms(self) -> None:
        result_with_echo = EquivalenceCheckResult(
            verdict=Verdict.EQUAL,
            observations=[obs(OracleVerdict.EQUAL)],
            effective_timeout_ms=3000,
        )
        use_case = EquivalenceVerificationUseCase(_StubChecker(result_with_echo))
        results = use_case.verify_batch(
            [EquivalenceInput(id="a", slow="1", fast="1", timeout_ms=3000)],
        )
        assert results[0].effective_timeout_ms == 3000
