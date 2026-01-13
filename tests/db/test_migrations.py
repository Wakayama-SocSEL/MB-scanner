"""DatabaseMigratorのテスト"""

from pathlib import Path
import sqlite3

import pytest

from mb_scanner.db.migrations import DatabaseMigrator, MigrationError


class TestDatabaseMigrator:
    """DatabaseMigratorクラスのテスト"""

    def test_add_js_lines_count_column_new(self, tmp_path: Path) -> None:
        """新規にjs_lines_countカラムを追加できる"""
        # Arrange: テスト用のデータベースを作成
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act: マイグレーションを実行
        result = migrator.add_js_lines_count_column()

        # Assert: カラムが追加されたことを確認
        assert result is True
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "js_lines_count" in columns
        conn.close()

    def test_add_js_lines_count_column_already_exists(self, tmp_path: Path) -> None:
        """既にjs_lines_countカラムが存在する場合はスキップする（冪等性）"""
        # Arrange: js_lines_countカラムが既に存在するデータベースを作成
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                js_lines_count INTEGER
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act: マイグレーションを実行
        result = migrator.add_js_lines_count_column()

        # Assert: 既に存在するためFalseが返される
        assert result is False

    def test_add_js_lines_count_column_dry_run(self, tmp_path: Path) -> None:
        """ドライランモードでは実際にカラムを追加しない"""
        # Arrange
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act: ドライランモードで実行
        result = migrator.add_js_lines_count_column(dry_run=True)

        # Assert: Trueが返されるがカラムは追加されていない
        assert result is True
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "js_lines_count" not in columns
        conn.close()

    def test_add_js_lines_count_column_database_not_found(self, tmp_path: Path) -> None:
        """データベースファイルが存在しない場合はエラーを発生させる"""
        # Arrange
        db_path = tmp_path / "nonexistent.db"
        migrator = DatabaseMigrator(db_path)

        # Act & Assert
        with pytest.raises(MigrationError, match="Database file not found"):
            migrator.add_js_lines_count_column()

    def test_run_all_migrations(self, tmp_path: Path) -> None:
        """全てのマイグレーションを実行できる"""
        # Arrange
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act
        results = migrator.run_all_migrations()

        # Assert: 実行された
        assert "add_js_lines_count_column" in results
        assert results["add_js_lines_count_column"] is True

        # カラムが追加されたことを確認
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "js_lines_count" in columns
        conn.close()

    def test_run_all_migrations_already_migrated(self, tmp_path: Path) -> None:
        """既にマイグレーション済みの場合はスキップされる"""
        # Arrange: 既にマイグレーション済みのデータベース
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                js_lines_count INTEGER
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act
        results = migrator.run_all_migrations()

        # Assert: スキップされた
        assert "add_js_lines_count_column" in results
        assert results["add_js_lines_count_column"] is False

    def test_run_all_migrations_dry_run(self, tmp_path: Path) -> None:
        """ドライランモードで全てのマイグレーションを確認できる"""
        # Arrange
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        migrator = DatabaseMigrator(db_path)

        # Act
        results = migrator.run_all_migrations(dry_run=True)

        # Assert
        assert "add_js_lines_count_column" in results
        assert results["add_js_lines_count_column"] is True

        # カラムは追加されていないことを確認
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "js_lines_count" not in columns
        conn.close()
