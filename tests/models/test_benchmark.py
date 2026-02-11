"""Tests for mb_scanner.models.benchmark"""

import json

from mb_scanner.models.benchmark import EquivalenceResult


class TestEquivalenceResultFormatOutput:
    """EquivalenceResult.format_outputのテスト"""

    def test_format_json_string_to_object(self) -> None:
        """JSON文字列の場合、JSONオブジェクトに変換される"""
        result = EquivalenceResult(
            id=1,
            status="equal",
            slow_output='{"VAR_1":1,"VAR_2":[1,2,3]}',
            fast_output='{"VAR_1":1,"VAR_2":[1,2,3]}',
            comparison_method="variables",
        )

        # model_dump_json()でシリアライズ
        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # slow_outputとfast_outputがJSONオブジェクトとして展開されていることを確認
        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["VAR_1"] == 1
        assert result_dict["slow_output"]["VAR_2"] == [1, 2, 3]

    def test_format_plain_text(self) -> None:
        """プレーンテキストの場合、文字列のまま保持される"""
        result = EquivalenceResult(
            id=1,
            status="equal",
            slow_output="Hello World",
            fast_output="Hello World",
            comparison_method="stdout",
        )

        # model_dump_json()でシリアライズ
        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # プレーンテキストは文字列のまま
        assert result_dict["slow_output"] == "Hello World"
        assert result_dict["fast_output"] == "Hello World"

    def test_format_null_value(self) -> None:
        """Noneの場合、Noneのまま返される"""
        result = EquivalenceResult(
            id=1,
            status="error",
            slow_output=None,
            fast_output=None,
            comparison_method="none",
        )

        # model_dump_json()でシリアライズ
        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # Noneはnullとして保持される
        assert result_dict["slow_output"] is None
        assert result_dict["fast_output"] is None

    def test_format_variables_method(self) -> None:
        """variablesメソッドの場合、JSONオブジェクトに変換される"""
        result = EquivalenceResult(
            id=2,
            status="not_equal",
            slow_output='{"VAR_5":1000000}',
            fast_output='{"VAR_5":1000000,"VAR_6":{"VAR_7":1,"VAR_8":2}}',
            comparison_method="variables",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # JSONオブジェクトとして展開されていることを確認
        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["VAR_5"] == 1000000
        assert result_dict["fast_output"]["VAR_5"] == 1000000
        assert result_dict["fast_output"]["VAR_6"]["VAR_7"] == 1
        assert result_dict["fast_output"]["VAR_6"]["VAR_8"] == 2

    def test_format_functions_method(self) -> None:
        """functionsメソッドの場合、JSONオブジェクトに変換される"""
        result = EquivalenceResult(
            id=3,
            status="equal",
            slow_output='{"result":42}',
            fast_output='{"result":42}',
            comparison_method="functions",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # JSONオブジェクトとして展開されていることを確認
        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["result"] == 42
        assert result_dict["fast_output"]["result"] == 42

    def test_format_stdout_with_json(self) -> None:
        """stdoutメソッドでJSON形式の場合、JSONオブジェクトに変換される"""
        result = EquivalenceResult(
            id=4,
            status="equal",
            slow_output='{"message":"test"}',
            fast_output='{"message":"test"}',
            comparison_method="stdout",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # JSON形式ならオブジェクトに変換される
        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["message"] == "test"

    def test_format_stdout_with_plain_text(self) -> None:
        """stdoutメソッドでプレーンテキストの場合、文字列のまま保持される"""
        result = EquivalenceResult(
            id=5,
            status="equal",
            slow_output="Output: 123",
            fast_output="Output: 123",
            comparison_method="stdout",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # プレーンテキストは文字列のまま
        assert result_dict["slow_output"] == "Output: 123"
        assert result_dict["fast_output"] == "Output: 123"

    def test_format_complex_nested_json(self) -> None:
        """複雑なネストされたJSONの場合もオブジェクトに変換される"""
        complex_json = '{"a":{"b":{"c":[1,2,3]}},"d":"test"}'
        result = EquivalenceResult(
            id=6,
            status="equal",
            slow_output=complex_json,
            fast_output=complex_json,
            comparison_method="variables",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # ネストされたJSON構造がオブジェクトとして展開されていることを確認
        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["a"]["b"]["c"] == [1, 2, 3]
        assert result_dict["slow_output"]["d"] == "test"

    def test_format_unicode_characters(self) -> None:
        """Unicode文字を含むJSON文字列が正しく変換される"""
        result = EquivalenceResult(
            id=7,
            status="equal",
            slow_output='{"message":"こんにちは"}',
            fast_output='{"message":"こんにちは"}',
            comparison_method="variables",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # Unicode文字が正しく保持される
        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["message"] == "こんにちは"

    def test_already_dict_object(self) -> None:
        """既にdictオブジェクトの場合、そのまま保持される"""
        result = EquivalenceResult(
            id=8,
            status="equal",
            slow_output={"VAR_1": 123, "VAR_2": [1, 2, 3]},
            fast_output={"VAR_1": 123, "VAR_2": [1, 2, 3]},
            comparison_method="variables",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        # dictオブジェクトがそのまま保持される
        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["VAR_1"] == 123
        assert result_dict["slow_output"]["VAR_2"] == [1, 2, 3]
