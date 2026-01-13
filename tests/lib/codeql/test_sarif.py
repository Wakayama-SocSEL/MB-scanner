"""SARIF解析とコード抽出機能のテスト"""

import json
from pathlib import Path
import shutil

import pytest

from mb_scanner.lib.codeql.sarif import SarifExtractor, SarifResult, extract_code_for_project

# フィクスチャのパス
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "sarif"
SAMPLE_SARIF = FIXTURES_DIR / "sample.sarif"
EMPTY_SARIF = FIXTURES_DIR / "empty_results.sarif"
SAMPLE_REPO = FIXTURES_DIR / "repository"


class TestSarifResult:
    """SarifResult データクラスのテスト"""

    def test_sarif_result_dataclass(self):
        """SarifResultのインスタンス化とフィールドアクセスをテスト"""
        result = SarifResult(
            id=0,
            file_path="src/example.js",
            start_line=10,
            end_line=20,
            start_column=5,
            end_column=15,
            message="Test message",
            severity="warning",
        )

        assert result.id == 0
        assert result.file_path == "src/example.js"
        assert result.start_line == 10
        assert result.end_line == 20
        assert result.start_column == 5
        assert result.end_column == 15
        assert result.message == "Test message"
        assert result.severity == "warning"

    def test_sarif_result_with_none_columns(self):
        """列情報がNoneの場合のテスト"""
        result = SarifResult(
            id=1,
            file_path="src/test.js",
            start_line=1,
            end_line=5,
            start_column=None,
            end_column=None,
            message="No column info",
            severity="error",
        )

        assert result.start_column is None
        assert result.end_column is None


class TestSarifExtractor:
    """SarifExtractor クラスのテスト"""

    def test_init(self):
        """SarifExtractorの初期化をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        assert extractor.sarif_path == SAMPLE_SARIF
        assert extractor.repository_path == SAMPLE_REPO

    def test_parse_sarif_valid(self):
        """正常なSARIFファイルの解析をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)
        results = extractor.parse_sarif()

        # 結果数の検証（endLine省略パターンを含めて4件）
        assert len(results) == 4

        # 最初の結果の検証（列情報あり）
        result0 = results[0]
        assert result0.id == 0
        assert result0.file_path == "src/example.js"
        assert result0.start_line == 5
        assert result0.end_line == 7
        assert result0.start_column == 10
        assert result0.end_column == 2
        assert result0.message == "This is a test detection."
        assert result0.severity == "warning"

        # 2番目の結果の検証（列情報なし）
        result1 = results[1]
        assert result1.id == 1
        assert result1.file_path == "src/example.js"
        assert result1.start_line == 10
        assert result1.end_line == 12
        assert result1.start_column is None
        assert result1.end_column is None
        assert result1.message == "Another test detection without columns."
        assert result1.severity == "error"

        # 3番目の結果の検証
        result2 = results[2]
        assert result2.id == 2
        assert result2.file_path == "src/utils.js"
        assert result2.start_line == 1
        assert result2.end_line == 3
        assert result2.message == "Detection in another file."
        assert result2.severity == "note"

        # 4番目の結果の検証（endLine省略パターン）
        result3 = results[3]
        assert result3.id == 3
        assert result3.file_path == "src/example.js"
        assert result3.start_line == 2
        assert result3.end_line == 2  # endLineが省略されているのでstartLineと同じ
        assert result3.start_column is None
        assert result3.end_column == 20
        assert result3.message == "Detection without endLine (single line)."
        assert result3.severity == "warning"

    def test_parse_sarif_empty_results(self):
        """検出結果が0件のSARIFファイルの処理をテスト"""
        extractor = SarifExtractor(sarif_path=EMPTY_SARIF, repository_path=SAMPLE_REPO)
        results = extractor.parse_sarif()

        assert len(results) == 0
        assert results == []

    def test_parse_sarif_file_not_found(self):
        """SARIFファイルが存在しない場合のエラーハンドリングをテスト"""
        extractor = SarifExtractor(
            sarif_path=FIXTURES_DIR / "nonexistent.sarif",
            repository_path=SAMPLE_REPO,
        )

        with pytest.raises(FileNotFoundError):
            extractor.parse_sarif()

    def test_extract_code_snippet_multi_line(self):
        """複数行のコードスニペット抽出をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = SarifResult(
            id=0,
            file_path="src/example.js",
            start_line=5,
            end_line=7,
            start_column=10,
            end_column=2,
            message="Test",
            severity="warning",
        )

        snippet = extractor.extract_code_snippet(result)

        # 行5-7の内容を確認（5行目は空行）
        expected_lines = [
            "",  # 5行目は空行
            "function testFunction() {",
            "  const x = 1;",
        ]
        assert snippet == "\n".join(expected_lines)

    def test_extract_code_snippet_single_line(self):
        """単一行のコードスニペット抽出をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = SarifResult(
            id=0,
            file_path="src/example.js",
            start_line=2,
            end_line=2,
            start_column=None,
            end_column=None,
            message="Test",
            severity="warning",
        )

        snippet = extractor.extract_code_snippet(result)

        assert snippet == "function hello() {"

    def test_extract_code_snippet_with_columns(self):
        """列情報がある場合のコードスニペット抽出をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = SarifResult(
            id=0,
            file_path="src/utils.js",
            start_line=1,
            end_line=3,
            start_column=1,
            end_column=2,
            message="Test",
            severity="warning",
        )

        snippet = extractor.extract_code_snippet(result)

        # 列情報があっても、現時点では行全体を取得
        expected_lines = [
            "function add(a, b) {",
            "  return a + b;",
            "}",
        ]
        assert snippet == "\n".join(expected_lines)

    def test_extract_code_snippet_file_not_found(self):
        """存在しないファイルの処理をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = SarifResult(
            id=0,
            file_path="src/nonexistent.js",
            start_line=1,
            end_line=5,
            start_column=None,
            end_column=None,
            message="Test",
            severity="warning",
        )

        snippet = extractor.extract_code_snippet(result)

        assert snippet == "[File not found]"

    def test_extract_code_snippet_line_out_of_range(self):
        """行番号が範囲外の場合の処理をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = SarifResult(
            id=0,
            file_path="src/example.js",
            start_line=100,
            end_line=200,
            start_column=None,
            end_column=None,
            message="Test",
            severity="warning",
        )

        snippet = extractor.extract_code_snippet(result)

        # 範囲外の場合は空文字列または特別なメッセージ
        assert snippet == "[Line out of range]"

    def test_parse_sarif_url_encoded_uri(self, tmp_path):
        """URLエンコードされたURIが正しくデコードされることをテスト"""
        # URLエンコードされたファイル名を持つSARIFを作成
        sarif_data = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "results": [
                        {
                            "message": {"text": "Test detection"},
                            "level": "warning",
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {
                                            "uri": "backup/067-bilibili%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9/test.js"
                                        },
                                        "region": {"startLine": 1, "endLine": 1},
                                    }
                                }
                            ],
                        }
                    ]
                }
            ],
        }

        sarif_path = tmp_path / "test.sarif"
        with sarif_path.open("w") as f:
            json.dump(sarif_data, f)

        extractor = SarifExtractor(sarif_path=sarif_path, repository_path=tmp_path)
        results = extractor.parse_sarif()

        assert len(results) == 1
        # URLデコードされたパスが取得されることを確認
        assert results[0].file_path == "backup/067-bilibili哔哩哔哩/test.js"

    def test_extract_code_snippet_build_artifact_skipped(self):
        """ビルド成果物がスキップされることをテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        # ビルド成果物のパスをテスト
        build_paths = [
            "build/setup.bundle.js",
            "dist/main.js",
            "out/index.js",
            ".next/static/chunks/main.js",
            "target/release/app",
        ]

        for path in build_paths:
            result = SarifResult(
                id=0,
                file_path=path,
                start_line=1,
                end_line=1,
                start_column=None,
                end_column=None,
                message="Test",
                severity="warning",
            )

            snippet = extractor.extract_code_snippet(result)
            assert snippet == "[Build artifact - skipped]", f"Failed for path: {path}"

    def test_extract_all_integration(self):
        """統合テスト：実際のSARIFファイルとリポジトリを使用"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = extractor.extract_all()

        # メタデータの検証
        assert "metadata" in result
        metadata = result["metadata"]
        assert "sarif_path" in metadata
        assert "repository_path" in metadata
        assert "total_results" in metadata
        assert "extraction_date" in metadata
        assert metadata["total_results"] == 4

        # 結果の検証
        assert "results" in result
        results = result["results"]
        assert len(results) == 4

        # 各結果にcode_snippetが含まれることを確認
        for res in results:
            assert "id" in res
            assert "file_path" in res
            assert "start_line" in res
            assert "end_line" in res
            assert "message" in res
            assert "severity" in res
            assert "code_snippet" in res

        # 最初の結果のコードスニペットを検証
        assert "function testFunction()" in results[0]["code_snippet"]

    def test_extract_all_empty_results(self):
        """空の結果に対するextract_allのテスト"""
        extractor = SarifExtractor(sarif_path=EMPTY_SARIF, repository_path=SAMPLE_REPO)

        result = extractor.extract_all()

        assert result["metadata"]["total_results"] == 0
        assert len(result["results"]) == 0

    def test_metadata_generation(self):
        """メタデータの正確性をテスト"""
        extractor = SarifExtractor(sarif_path=SAMPLE_SARIF, repository_path=SAMPLE_REPO)

        result = extractor.extract_all()
        metadata = result["metadata"]

        # パスの検証
        assert str(SAMPLE_SARIF) in metadata["sarif_path"]
        assert str(SAMPLE_REPO) in metadata["repository_path"]

        # 総結果数の検証
        assert metadata["total_results"] == 4

        # タイムスタンプの形式検証
        assert "extraction_date" in metadata
        # ISO 8601形式かどうかを簡易チェック
        assert "T" in metadata["extraction_date"]


class TestExtractCodeForProject:
    """extract_code_for_project 関数のテスト"""

    def test_extract_code_for_project_success(self, tmp_path):
        """正常系のテスト：コード抽出が成功する場合"""
        # テスト用のディレクトリ構成を作成
        query_id = "test_query"
        project_name = "test-project"

        # SARIFディレクトリの作成
        sarif_dir = tmp_path / "sarif" / query_id
        sarif_dir.mkdir(parents=True)

        # サンプルSARIFファイルをコピー
        sarif_file = sarif_dir / f"{project_name}.sarif"
        shutil.copy(SAMPLE_SARIF, sarif_file)

        # リポジトリディレクトリをコピー
        repo_dir = tmp_path / "repos" / project_name
        repo_dir.mkdir(parents=True)
        shutil.copytree(SAMPLE_REPO, repo_dir, dirs_exist_ok=True)

        # 出力ディレクトリ
        output_dir = tmp_path / "output"

        # 関数を実行
        result = extract_code_for_project(
            query_id=query_id,
            project_name=project_name,
            sarif_base_dir=tmp_path / "sarif",
            repository_base_dir=tmp_path / "repos",
            output_base_dir=output_dir,
        )

        # 結果の検証
        assert result["status"] == "success"
        assert result["project"] == project_name
        assert result["output_path"] is not None
        assert result["result_count"] == 4
        assert result["error"] is None

        # 出力ファイルが作成されたことを確認
        output_file = Path(result["output_path"])
        assert output_file.exists()

        # 出力ファイルの内容を確認
        with output_file.open() as f:
            data = json.load(f)

        assert "metadata" in data
        assert "results" in data
        assert len(data["results"]) == 4

    def test_extract_code_for_project_sarif_not_found(self, tmp_path):
        """SARIFファイルが存在しない場合のテスト"""
        query_id = "test_query"
        project_name = "nonexistent-project"

        # リポジトリディレクトリは作成するがSARIFファイルは作成しない
        repo_dir = tmp_path / "repos" / project_name
        repo_dir.mkdir(parents=True)

        result = extract_code_for_project(
            query_id=query_id,
            project_name=project_name,
            sarif_base_dir=tmp_path / "sarif",
            repository_base_dir=tmp_path / "repos",
            output_base_dir=tmp_path / "output",
        )

        # 結果の検証
        assert result["status"] == "skipped"
        assert result["project"] == project_name
        assert result["output_path"] is None
        assert result["result_count"] is None
        assert result["error"] is not None
        assert "SARIF file not found" in result["error"]

    def test_extract_code_for_project_repository_not_found(self, tmp_path):
        """リポジトリが存在しない場合のテスト"""
        query_id = "test_query"
        project_name = "test-project"

        # SARIFファイルは作成するがリポジトリは作成しない
        sarif_dir = tmp_path / "sarif" / query_id
        sarif_dir.mkdir(parents=True)

        sarif_file = sarif_dir / f"{project_name}.sarif"
        shutil.copy(SAMPLE_SARIF, sarif_file)

        result = extract_code_for_project(
            query_id=query_id,
            project_name=project_name,
            sarif_base_dir=tmp_path / "sarif",
            repository_base_dir=tmp_path / "repos",
            output_base_dir=tmp_path / "output",
        )

        # 結果の検証
        assert result["status"] == "skipped"
        assert result["project"] == project_name
        assert result["output_path"] is None
        assert result["result_count"] is None
        assert result["error"] is not None
        assert "Repository not found" in result["error"]

    def test_extract_code_for_project_creates_output_directory(self, tmp_path):
        """出力ディレクトリが自動的に作成されることを確認"""
        query_id = "test_query"
        project_name = "test-project"

        # テスト用のファイル構成を作成
        sarif_dir = tmp_path / "sarif" / query_id
        sarif_dir.mkdir(parents=True)

        sarif_file = sarif_dir / f"{project_name}.sarif"
        shutil.copy(SAMPLE_SARIF, sarif_file)

        repo_dir = tmp_path / "repos" / project_name
        repo_dir.mkdir(parents=True)
        shutil.copytree(SAMPLE_REPO, repo_dir, dirs_exist_ok=True)

        # 出力ディレクトリは作成しない
        output_dir = tmp_path / "output" / "nested" / "path"

        result = extract_code_for_project(
            query_id=query_id,
            project_name=project_name,
            sarif_base_dir=tmp_path / "sarif",
            repository_base_dir=tmp_path / "repos",
            output_base_dir=output_dir,
        )

        # 結果の検証
        assert result["status"] == "success"

        # 出力ディレクトリが作成されたことを確認
        assert result["output_path"] is not None
        output_file = Path(result["output_path"])
        assert output_file.parent.exists()
        assert output_file.exists()
