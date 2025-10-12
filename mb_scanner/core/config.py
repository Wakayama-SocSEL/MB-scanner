"""プロジェクトで使用する環境設定モジュール

このモジュールは、プロジェクト全体で使用する設定値や定数を定義します。
主に、データセットのパスやディレクトリ構成を管理するために使用されます。
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション全体の設定を管理するクラス

    環境変数や.envファイルから自動で値を読み込む
    """

    # .envファイルを読み込む設定と、環境変数の接頭辞（プレフィックス）を指定
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MB_SCANNER_")

    # ユーザーが環境変数で直接指定できる値
    data_dir: Path | None = None  # 例: MB_SCANNER_DATA_DIR=/path/to/data
    db_file: Path | None = None  # 例: MB_SCANNER_DB_FILE=/path/to/data/app.db

    @property
    def effective_data_dir(self) -> Path:
        """データディレクトリの有効なパスを返す"""
        # data_dirが指定されていなければ、現在の作業ディレクトリに 'data' を作成
        path = self.data_dir or Path.cwd() / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def effective_db_file(self) -> Path:
        """データベースファイルの有効なパスを返す"""
        # db_fileが指定されていればそれを使い、なければデフォルトパスを生成
        return self.db_file or self.effective_data_dir / "mb_scanner.db"

    @property
    def database_url(self) -> str:
        """SQLAlchemy用のデータベースURLを返す"""
        return f"sqlite:///{self.effective_db_file.resolve()}"


# シングルトンとしてインスタンスを作成
settings = Settings()
