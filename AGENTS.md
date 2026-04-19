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

TypeScript 側 (`mb-analyzer/`) も ESLint `import/no-restricted-paths` で依存方向を機械強制 (`mise run lint-analyzer`)。詳細は [`ai-guide/architecture/`](ai-guide/architecture/index.md) 参照。言語別の参照ドキュメント:
- Python 側の詳細: [`mb-scanner.md`](ai-guide/architecture/mb-scanner.md)
- TypeScript 側の詳細: [`mb-analyzer.md`](ai-guide/architecture/mb-analyzer.md)
- 両言語をまたぐ JSON 契約: [`index.md`](ai-guide/architecture/index.md)

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

## 主要 CLI コマンド
- `mbs check-equivalence --input trip.json`: 1 トリプル (setup, slow, fast) の等価性検証。内部で `mb-analyzer/dist/cli.js` を subprocess 起動。事前に `mise run build-analyzer` が必要。終了コード equal=0 / not_equal=1 / error=2。
- `mbs check-equivalence-batch --input trips.jsonl --output results.jsonl --workers -1`: 複数トリプルの一括検証。JSONL 入出力、Python 側 `ThreadPoolExecutor` で並列化 (`workers=-1` で `os.cpu_count()`)。各行に `id` / `timeout_ms` を含められる。Node 側は 1 バッチ 1 subprocess でトリプルを逐次処理するため、単発 API × N 回より起動コストが圧縮される。結果の `effective_timeout_ms` で checker が実際に使った timeout_ms を検証可能。終了コード 正常=0 / I/O・バリデーション失敗=2。
- `mbs codeql ...`, `mbs github ...` 等: 既存コマンド
