"""VisualizationServiceのテストモジュール"""

from datetime import UTC, datetime
import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from mb_scanner.models.project import Project
from mb_scanner.services.visualization_service import VisualizationService


@pytest.fixture
def visualization_service(test_db: Session) -> VisualizationService:
    """VisualizationServiceのインスタンスを提供するフィクスチャ

    Args:
        test_db: テスト用DBセッション

    Returns:
        VisualizationService: テスト用サービスインスタンス
    """
    return VisualizationService(test_db)


@pytest.fixture
def sample_projects(test_db: Session) -> list[Project]:
    """テスト用のプロジェクトデータを作成するフィクスチャ

    Args:
        test_db: テスト用DBセッション

    Returns:
        list[Project]: 作成されたプロジェクトのリスト
    """
    projects = [
        Project(
            full_name="test/repo1",
            url="https://github.com/test/repo1",
            stars=100,
            language="JavaScript",
            description="Test repo 1",
            last_commit_date=datetime.now(UTC),
            js_lines_count=1000,
        ),
        Project(
            full_name="test/repo2",
            url="https://github.com/test/repo2",
            stars=200,
            language="JavaScript",
            description="Test repo 2",
            last_commit_date=datetime.now(UTC),
            js_lines_count=2000,
        ),
        Project(
            full_name="test/repo3",
            url="https://github.com/test/repo3",
            stars=150,
            language="JavaScript",
            description="Test repo 3",
            last_commit_date=datetime.now(UTC),
            js_lines_count=1500,
        ),
        Project(
            full_name="test/repo4",
            url="https://github.com/test/repo4",
            stars=300,
            language="JavaScript",
            description="Test repo 4",
            last_commit_date=datetime.now(UTC),
            js_lines_count=3000,
        ),
        Project(
            full_name="test/repo5",
            url="https://github.com/test/repo5",
            stars=50,
            language="JavaScript",
            description="Test repo 5 with null js_lines_count",
            last_commit_date=datetime.now(UTC),
            js_lines_count=None,  # Nullケース
        ),
    ]
    for project in projects:
        test_db.add(project)
    test_db.commit()
    return projects


@pytest.fixture
def sample_json_path(tmp_path: Path) -> Path:
    """テスト用のJSONファイルパスを提供するフィクスチャ

    Args:
        tmp_path: pytestが提供する一時ディレクトリ

    Returns:
        Path: 作成されたJSONファイルのパス
    """
    json_file = tmp_path / "sample_query_result.json"
    data = {
        "query_id": "id_test_001",
        "total_projects": 5,
        "results": {
            "test/repo1": 10,
            "test/repo2": 25,
            "test/repo3": 5,
            "test/repo4": 50,
            "test/repo5": 0,
        },
        "generated_at": "2025-01-15T00:00:00.000000+00:00",
        "threshold": 0,
    }
    json_file.write_text(json.dumps(data, indent=2))
    return json_file


class TestLoadQueryResults:
    """load_query_resultsメソッドのテスト"""

    def test_load_query_results_success(
        self, visualization_service: VisualizationService, sample_json_path: Path
    ) -> None:
        """正常なJSONファイルの読み込みテスト"""
        result = visualization_service.load_query_results(sample_json_path)

        assert result["query_id"] == "id_test_001"
        assert result["total_projects"] == 5
        assert len(result["results"]) == 5
        assert result["results"]["test/repo1"] == 10
        assert result["results"]["test/repo2"] == 25

    def test_load_query_results_file_not_found(self, visualization_service: VisualizationService) -> None:
        """存在しないファイルのエラー処理テスト"""
        non_existent_path = Path("/non/existent/path.json")

        with pytest.raises(FileNotFoundError):
            visualization_service.load_query_results(non_existent_path)

    def test_load_query_results_invalid_json(self, visualization_service: VisualizationService, tmp_path: Path) -> None:
        """不正なJSONのエラー処理テスト"""
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            visualization_service.load_query_results(invalid_json_file)


class TestGetScatterData:
    """get_scatter_dataメソッドのテスト"""

    def test_get_scatter_data_with_valid_projects(
        self,
        visualization_service: VisualizationService,
        sample_projects: list[Project],
        sample_json_path: Path,
    ) -> None:
        """有効なプロジェクトデータの取得テスト"""
        data = visualization_service.get_scatter_data(sample_json_path)

        # repo5はjs_lines_countがNullなのでスキップされる
        assert len(data) == 4

        # データの形式確認: (js_lines_count, detection_count, full_name)
        assert all(len(item) == 3 for item in data)
        assert all(isinstance(item[0], int) for item in data)
        assert all(isinstance(item[1], int) for item in data)
        assert all(isinstance(item[2], str) for item in data)

        # 具体的な値の確認
        data_dict = {item[2]: (item[0], item[1]) for item in data}
        assert data_dict["test/repo1"] == (1000, 10)
        assert data_dict["test/repo2"] == (2000, 25)
        assert data_dict["test/repo3"] == (1500, 5)
        assert data_dict["test/repo4"] == (3000, 50)

    def test_get_scatter_data_with_missing_projects(
        self, visualization_service: VisualizationService, sample_json_path: Path
    ) -> None:
        """DBに存在しないプロジェクトの処理テスト（スキップされる）"""
        # sample_projectsフィクスチャを使わないことで、DBは空の状態
        data = visualization_service.get_scatter_data(sample_json_path)

        # DBにプロジェクトが存在しないため、全てスキップされる
        assert len(data) == 0

    def test_get_scatter_data_with_null_js_lines(
        self,
        visualization_service: VisualizationService,
        test_db: Session,
        sample_json_path: Path,
    ) -> None:
        """js_lines_countがNullの場合の処理テスト（スキップされる）"""
        # js_lines_countがNullのプロジェクトのみ作成
        project = Project(
            full_name="test/repo1",
            url="https://github.com/test/repo1",
            stars=100,
            language="JavaScript",
            description="Test repo with null js_lines_count",
            last_commit_date=datetime.now(UTC),
            js_lines_count=None,
        )
        test_db.add(project)
        test_db.commit()

        data = visualization_service.get_scatter_data(sample_json_path)

        # js_lines_countがNullなのでスキップされる
        assert len(data) == 0

    def test_get_scatter_data_empty_results(
        self,
        visualization_service: VisualizationService,
        sample_projects: list[Project],
        tmp_path: Path,
    ) -> None:
        """空の結果の処理テスト"""
        empty_json_file = tmp_path / "empty_results.json"
        data = {
            "query_id": "id_empty",
            "total_projects": 0,
            "results": {},
            "generated_at": "2025-01-15T00:00:00.000000+00:00",
            "threshold": 0,
        }
        empty_json_file.write_text(json.dumps(data))

        result = visualization_service.get_scatter_data(empty_json_file)

        assert len(result) == 0
