"""データベースマイグレーション管理モジュール

このモジュールでは、データベーススキーマの変更を安全に実行するための
マイグレーション機能を提供します。
"""

import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """マイグレーション実行時のエラー"""


class DatabaseMigrator:
    """データベースマイグレーションを管理するクラス"""

    def __init__(self, database_path: Path) -> None:
        """DatabaseMigratorを初期化する

        Args:
            database_path: データベースファイルのパス
        """
        self.database_path = database_path

    def _column_exists(self, conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
        """テーブルに指定されたカラムが存在するかチェックする

        Args:
            conn: データベース接続
            table_name: テーブル名
            column_name: カラム名

        Returns:
            bool: カラムが存在する場合True
        """
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns

    def add_js_lines_count_column(self, *, dry_run: bool = False) -> bool:
        """projectsテーブルにjs_lines_countカラムを追加する

        Args:
            dry_run: Trueの場合、実際には実行せず確認のみ行う

        Returns:
            bool: マイグレーションが実行された場合True、既に存在する場合False

        Raises:
            MigrationError: マイグレーション実行時にエラーが発生した場合
        """
        if not self.database_path.exists():
            msg = f"Database file not found: {self.database_path}"
            raise MigrationError(msg)

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # カラムが既に存在するかチェック
            if self._column_exists(conn, "projects", "js_lines_count"):
                logger.info("Column 'js_lines_count' already exists in 'projects' table")
                conn.close()
                return False

            if dry_run:
                logger.info("[DRY RUN] Would execute: ALTER TABLE projects ADD COLUMN js_lines_count INTEGER")
                conn.close()
                return True

            # マイグレーションを実行
            logger.info("Adding 'js_lines_count' column to 'projects' table...")
            cursor.execute("ALTER TABLE projects ADD COLUMN js_lines_count INTEGER")
            conn.commit()
            logger.info("✓ Migration completed successfully")
            conn.close()
            return True

        except sqlite3.Error as e:
            msg = f"Failed to execute migration: {e}"
            logger.error(msg)
            raise MigrationError(msg) from e

    def run_all_migrations(self, *, dry_run: bool = False) -> dict[str, bool]:
        """全てのマイグレーションを実行する

        Args:
            dry_run: Trueの場合、実際には実行せず確認のみ行う

        Returns:
            dict[str, bool]: マイグレーション名とその実行結果の辞書

        Raises:
            MigrationError: マイグレーション実行時にエラーが発生した場合
        """
        results: dict[str, bool] = {}

        # 現在のマイグレーション一覧
        migrations = [
            ("add_js_lines_count_column", self.add_js_lines_count_column),
        ]

        for name, migration_func in migrations:
            logger.info(f"Running migration: {name}")
            try:
                executed = migration_func(dry_run=dry_run)
                results[name] = executed
            except MigrationError:
                # エラーは既にログ出力されているのでre-raise
                raise

        return results
