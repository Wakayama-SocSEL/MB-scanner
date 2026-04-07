"""Tests for mb_scanner.models.benchmark"""

import json

from mb_scanner.cli.benchmark import compact_json_array
from mb_scanner.models.benchmark import StrategyResult


class TestStrategyResultFormatOutput:
    """StrategyResult.format_outputのテスト"""

    def test_format_json_string_to_object(self) -> None:
        """JSON文字列の場合、JSONオブジェクトに変換される"""
        result = StrategyResult(
            comparison_method="variables",
            status="equal",
            slow_output='{"VAR_1":1,"VAR_2":[1,2,3]}',
            fast_output='{"VAR_1":1,"VAR_2":[1,2,3]}',
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["VAR_1"] == 1
        assert result_dict["slow_output"]["VAR_2"] == [1, 2, 3]

    def test_format_plain_text(self) -> None:
        """プレーンテキストの場合、文字列のまま保持される"""
        result = StrategyResult(
            comparison_method="stdout",
            status="equal",
            slow_output="Hello World",
            fast_output="Hello World",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert result_dict["slow_output"] == "Hello World"
        assert result_dict["fast_output"] == "Hello World"

    def test_format_null_value(self) -> None:
        """Noneの場合、Noneのまま返される"""
        result = StrategyResult(
            comparison_method="functions",
            status="error",
            slow_output=None,
            fast_output=None,
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert result_dict["slow_output"] is None
        assert result_dict["fast_output"] is None

    def test_format_variables_method(self) -> None:
        """variables戦略の場合、JSONオブジェクトに変換される"""
        result = StrategyResult(
            comparison_method="variables",
            status="not_equal",
            slow_output='{"VAR_5":1000000}',
            fast_output='{"VAR_5":1000000,"VAR_6":{"VAR_7":1,"VAR_8":2}}',
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["VAR_5"] == 1000000
        assert result_dict["fast_output"]["VAR_5"] == 1000000
        assert result_dict["fast_output"]["VAR_6"]["VAR_7"] == 1
        assert result_dict["fast_output"]["VAR_6"]["VAR_8"] == 2

    def test_format_functions_method(self) -> None:
        """functions戦略の場合、JSONオブジェクトに変換される"""
        result = StrategyResult(
            comparison_method="functions",
            status="not_equal",
            slow_output='{"result":42}',
            fast_output='{"result":99}',
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["result"] == 42
        assert result_dict["fast_output"]["result"] == 99

    def test_format_stdout_with_json(self) -> None:
        """stdout戦略でJSON形式の場合、JSONオブジェクトに変換される"""
        result = StrategyResult(
            comparison_method="stdout",
            status="not_equal",
            slow_output='{"message":"test"}',
            fast_output='{"message":"other"}',
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert isinstance(result_dict["fast_output"], dict)
        assert result_dict["slow_output"]["message"] == "test"

    def test_format_stdout_with_plain_text(self) -> None:
        """stdout戦略でプレーンテキストの場合、文字列のまま保持される"""
        result = StrategyResult(
            comparison_method="stdout",
            status="not_equal",
            slow_output="Output: 123",
            fast_output="Output: 456",
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert result_dict["slow_output"] == "Output: 123"
        assert result_dict["fast_output"] == "Output: 456"

    def test_format_complex_nested_json(self) -> None:
        """複雑なネストされたJSONの場合もオブジェクトに変換される"""
        complex_json = '{"a":{"b":{"c":[1,2,3]}},"d":"test"}'
        result = StrategyResult(
            comparison_method="variables",
            status="not_equal",
            slow_output=complex_json,
            fast_output=complex_json,
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["a"]["b"]["c"] == [1, 2, 3]
        assert result_dict["slow_output"]["d"] == "test"

    def test_format_unicode_characters(self) -> None:
        """Unicode文字を含むJSON文字列が正しく変換される"""
        result = StrategyResult(
            comparison_method="stdout",
            status="not_equal",
            slow_output='{"message":"こんにちは"}',
            fast_output='{"message":"さようなら"}',
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["message"] == "こんにちは"

    def test_already_dict_object(self) -> None:
        """既にdictオブジェクトの場合、そのまま保持される"""
        result = StrategyResult(
            comparison_method="variables",
            status="not_equal",
            slow_output={"VAR_1": 123, "VAR_2": [1, 2, 3]},
            fast_output={"VAR_1": 999, "VAR_2": [1, 2, 3]},
        )

        result_json = result.model_dump_json(indent=2)
        result_dict = json.loads(result_json)

        assert isinstance(result_dict["slow_output"], dict)
        assert result_dict["slow_output"]["VAR_1"] == 123
        assert result_dict["slow_output"]["VAR_2"] == [1, 2, 3]


class TestCompactJsonArray:
    """compact_json_array()関数のテスト"""

    def test_compact_primitive_number_array(self) -> None:
        """数値のみの配列がコンパクト化される"""
        input_str = "[\n  1,\n  2,\n  3\n]"
        expected = "[1, 2, 3]"
        assert compact_json_array(input_str) == expected

    def test_compact_primitive_string_array(self) -> None:
        """文字列のみの配列がコンパクト化される"""
        input_str = '[\n  "a",\n  "b",\n  "c"\n]'
        expected = '["a", "b", "c"]'
        assert compact_json_array(input_str) == expected

    def test_object_array_not_compacted(self) -> None:
        """オブジェクトを含む配列はコンパクト化されない"""
        # シンプルなオブジェクト配列
        input_str = '[\n  {\n    "key": "value"\n  }\n]'
        # オブジェクトを含む配列は変更されない
        assert compact_json_array(input_str) == input_str

    def test_object_array_without_nested_arrays(self) -> None:
        """ネスト配列を含まないオブジェクト配列はコンパクト化されない（id_2のケース）"""
        # id_2と同様のパターン: オブジェクトを含むが、内部に配列はない
        input_str = '[\n  {\n    "comparison_method": "variables",\n    "status": "not_equal"\n  }\n]'
        # オブジェクトを含むため、コンパクト化されない
        assert compact_json_array(input_str) == input_str

    def test_nested_array_inner_compacted(self) -> None:
        """ネスト配列の内側のプリミティブ配列のみコンパクト化される"""
        input_str = "[\n  1,\n  [\n    2,\n    3\n  ]\n]"
        # 内側の [2, 3] はコンパクト化されるが、外側（数値とネスト配列の混在）はそのまま
        expected = "[\n  1,\n  [2, 3]\n]"
        assert compact_json_array(input_str) == expected

    def test_object_with_primitive_array_property(self) -> None:
        """オブジェクト内のプリミティブ配列プロパティはコンパクト化される"""
        input_str = """{
  "data": [\n    1,\n    2,\n    3\n  ]
}"""
        expected = """{
  "data": [1, 2, 3]
}"""
        assert compact_json_array(input_str) == expected

    def test_empty_array(self) -> None:
        """空の配列もコンパクト化される"""
        input_str = "[\n]"
        expected = "[]"
        assert compact_json_array(input_str) == expected

    def test_mixed_primitive_array(self) -> None:
        """混在するプリミティブ値の配列がコンパクト化される"""
        input_str = '[\n  1,\n  "text",\n  true,\n  null\n]'
        expected = '[1, "text", true, null]'
        assert compact_json_array(input_str) == expected
