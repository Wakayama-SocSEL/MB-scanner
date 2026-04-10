# AGENTS.md

## プロジェクト概要
MB-Scanner: GitHubリポジトリを検索し、CodeQLを実行するバッチプラットフォーム。

## 技術スタック
- **言語**: Python 3.13+
- **CLIフレームワーク**: `typer` (コマンドラインインターフェース構築)
- **データベース**: SQLite + `sqlalchemy` (ORM)
- **データ/設定管理**: `pydantic` (バリデーション), `pydantic-settings` (.env管理)
- **外部連携**: `PyGithub` (GitHub API), `subprocess` (CodeQL CLI実行)
- **開発ツール**:
  - `uv` (パッケージ管理)
  - `just` (タスクランナー)
  - `ruff` (Lint/Format)
  - `pyright` (型チェック)
  - `pytest` (テスト)

## 重要なコーディング規約
- **型定義**: `Any`型は禁止。外部データには`Pydantic`、内部データには`TypedDict`を使用すること。
- **Lint/Format**: `ruff`の設定に従うこと。
- **テスト**: 新機能には必ず`pytest`を作成すること。

