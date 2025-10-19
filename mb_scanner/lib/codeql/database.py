"""CodeQLデータベース管理モジュール

このモジュールでは、CodeQLデータベースの管理機能を提供します。
"""

import logging
from pathlib import Path
import shutil

from mb_scanner.lib.codeql.command import CodeQLCLI

logger = logging.getLogger(__name__)


class CodeQLDatabaseManager:
    """CodeQLデータベースの管理クラス

    データベースのパス生成、存在チェック、作成などの機能を提供します。
    """

    def __init__(self, cli: CodeQLCLI, base_dir: Path) -> None:
        """CodeQLDatabaseManagerを初期化する

        Args:
            cli: CodeQLCLIインスタンス
            base_dir: DBの保存先ベースディレクトリ
        """
        self.cli = cli
        self.base_dir = base_dir

    def get_database_path(self, project_full_name: str) -> Path:
        """プロジェクト名からDBパスを生成する

        Args:
            project_full_name: プロジェクト名（owner/repo形式）

        Returns:
            Path: DBの保存先パス

        Examples:
            >>> manager = CodeQLDatabaseManager(cli, Path("/data/codeql-dbs"))
            >>> manager.get_database_path("facebook/react")
            Path('/data/codeql-dbs/facebook-react')
        """
        # "facebook/react" -> "facebook-react"
        safe_name = project_full_name.replace("/", "-")
        return self.base_dir / safe_name

    def database_exists(self, project_full_name: str) -> bool:
        """DBが既に存在するかチェックする

        Args:
            project_full_name: プロジェクト名（owner/repo形式）

        Returns:
            bool: DBが存在する場合True、存在しない場合False
        """
        db_path = self.get_database_path(project_full_name)
        exists = db_path.exists()
        logger.debug("Database exists check for %s: %s", project_full_name, exists)
        return exists

    def create_database(
        self,
        project_full_name: str,
        source_root: Path,
        language: str,
        *,
        threads: int | None = None,
        ram: int | None = None,
        force: bool = False,
    ) -> Path:
        """プロジェクトのCodeQL DBを作成する

        Args:
            project_full_name: プロジェクト名（owner/repo形式）
            source_root: ソースコードのルートディレクトリ
            language: 解析言語
            threads: 使用するスレッド数
            ram: 使用するRAM（MB）
            force: 既存DBを削除して再作成するか

        Returns:
            Path: 作成されたDBのパス

        Raises:
            FileExistsError: DBが既に存在し、force=Falseの場合
            FileNotFoundError: source_rootが存在しない場合
            subprocess.CalledProcessError: DB作成に失敗した場合
        """
        db_path = self.get_database_path(project_full_name)

        # 既存DBのチェック
        if db_path.exists():
            if not force:
                error_msg = f"Database already exists: {db_path}. Use force=True to overwrite."
                logger.error(error_msg)
                raise FileExistsError(error_msg)

            logger.warning("Removing existing database: %s", db_path)
            shutil.rmtree(db_path)

        # DB作成
        self.cli.create_database(
            database_path=db_path,
            source_root=source_root,
            language=language,
            threads=threads,
            ram=ram,
        )

        logger.info("Created CodeQL database for %s at %s", project_full_name, db_path)
        return db_path
