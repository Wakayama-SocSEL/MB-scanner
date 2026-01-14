"""可視化用のデータ取得・結合サービス

このモジュールでは、CodeQLクエリ結果とプロジェクトデータを結合して、
可視化に必要なデータを提供します。
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from mb_scanner.services.project_service import ProjectService


class VisualizationService:
    """可視化用データを提供するサービスクラス

    JSONファイルからCodeQLクエリ結果を読み込み、
    データベースからプロジェクト情報を取得して結合します。
    """

    def __init__(self, db: Session) -> None:
        """VisualizationServiceを初期化する

        Args:
            db: SQLAlchemyのセッションオブジェクト
        """
        self.db = db
        self.project_service = ProjectService(db)

    def load_query_results(self, json_path: Path) -> dict[str, Any]:
        """JSONファイルからクエリ結果を読み込む

        Args:
            json_path: クエリ結果のJSONファイルパス

        Returns:
            dict: クエリ結果の辞書

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            json.JSONDecodeError: JSONのパースに失敗した場合
        """
        if not json_path.exists():
            msg = f"File not found: {json_path}"
            raise FileNotFoundError(msg)

        with json_path.open() as f:
            return json.load(f)

    def get_scatter_data(self, json_path: Path) -> list[tuple[int, int, str]]:
        """散布図用のデータを取得する

        JSONファイルからクエリ結果を読み込み、データベースから対応する
        プロジェクトのjs_lines_countを取得して結合します。

        Args:
            json_path: クエリ結果のJSONファイルパス

        Returns:
            list[tuple[int, int, str]]: (js_lines_count, detection_count, full_name)のリスト
            js_lines_countがNullのプロジェクトやDBに存在しないプロジェクトはスキップされます。
        """
        # JSONファイルからクエリ結果を読み込む
        query_results = self.load_query_results(json_path)
        results_dict = query_results.get("results", {})

        scatter_data: list[tuple[int, int, str]] = []

        # 各プロジェクトの結果を処理
        for full_name, detection_count in results_dict.items():
            # データベースからプロジェクトを取得
            project = self.project_service.get_project_by_full_name(full_name)

            # プロジェクトが存在しない、またはjs_lines_countがNullの場合はスキップ
            if project is None or project.js_lines_count is None:
                continue

            # データを追加
            scatter_data.append((project.js_lines_count, detection_count, full_name))

        return scatter_data
