# AGENTS.md

## プロジェクト概要
MB-Scanner: GitHubリポジトリを検索し、CodeQLを実行するバッチプラットフォーム。

## アーキテクチャ
Clean Architecture 4層構造を採用。依存は常に内側に向かう。
- **domain** (最内層): エンティティ（Pydantic BaseModel）+ ポート（Protocol）
- **use_cases**: ビジネスロジック。Protocol 経由で DI。
- **adapters**: CLI（composition root）、Repository、Gateway
- **infrastructure** (最外層): ORM、DB接続、設定、ロギング

依存方向の自動検証: `mise run check-arch`（import-linter）

## 技術スタック
- **言語**: Python 3.13+
- **CLIフレームワーク**: `typer` (コマンドラインインターフェース構築)
- **データベース**: SQLite + `sqlalchemy` (ORM)
- **データ/設定管理**: `pydantic` (バリデーション), `pydantic-settings` (.env管理)
- **外部連携**: `PyGithub` (GitHub API), `subprocess` (CodeQL CLI実行)
- **開発ツール**:
  - `uv` (パッケージ管理)
  - `mise` (タスクランナー + ツールバージョン管理)
  - `ruff` (Lint/Format)
  - `pyright` (型チェック)
  - `pytest` (テスト)
  - `import-linter` (アーキテクチャ検証)

## 重要なコーディング規約
- **型定義**: `Any`型は禁止。外部データには`Pydantic`、内部データには`TypedDict`を使用すること。
- **ドメインモデル**: `domain/entities/` に Pydantic BaseModel で定義。dataclass は使わない。
- **依存方向**: use_cases は具象アダプターを import しない。Protocol 経由で DI。
- **命名**: GitHubリポジトリは `Project` と呼ぶ（`Repository` は DB パターン用語）。
- **Lint/Format**: `ruff`の設定に従うこと。
- **テスト**: 新機能には必ず`pytest`を作成すること。
