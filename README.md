# MB-Scanner

MB-Scanner は、GitHub 上の多数の公開 JavaScript リポジトリに対して、任意の CodeQL クエリを体系的かつ自動的に実行するためのバッチプラットフォームです。MB-search が生成したクエリや手動で作成したクエリの有効性を、実世界のコードベースで検証し、定量・定性的なデータを収集します。

## 目的
- MB-search が生成した CodeQL クエリの実用性を検証し、フィードバックループを構築する。
- コード品質・セキュリティに関する研究向けのデータセットを蓄積する。

## 技術スタック
| カテゴリ | 技術 | 理由 |
| --- | --- | --- |
| 言語 | Python 3.13+ | ライブラリが豊富で、外部コマンド連携が容易。 |
| データベース | SQLite | サーバーレスでバッチ処理の進捗管理と再開が簡単。 |
| ORM | SQLAlchemy | SQL を直接書かずに安全で保守しやすいコードを実現。 |
| GitHub API | `PyGithub` | 条件に合うリポジトリを効率よく取得。 |
| 外部ツール実行 | `subprocess` | `git clone` や `codeql` コマンドを柔軟に呼び出す。 |
| 開発支援 | `uv`, `just` | パッケージ管理とタスク運用を統一。 |

## インストール

このプロジェクトは [uv](https://docs.astral.sh/uv/) を使用して依存関係を管理しています。

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/MB-Scanner.git
cd MB-Scanner

# 依存関係のインストール
just python-deps
```

### 環境変数の設定

MB-Scanner を使用するには、GitHub API トークンが必要です。`.env.sample` を参考に環境変数を設定してください。

```bash
# .env.sample をコピーして .env ファイルを作成
cp .env.sample .env
```

`.env` ファイルを開き、GitHub API トークンを設定します：

```bash
# GitHub API Token（必須）
GITHUB_TOKEN="your_github_token_here"
```

GitHub Personal Access Token は [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) から取得できます（`public_repo` スコープが必要）。

その他のオプション設定については `.env.sample` を参照してください。

## 基本的な使い方

### リポジトリの検索と保存

```bash
# デフォルト設定で実行（JavaScript, 100+ stars, 365日以内の更新）
mb-scanner search
```

### CodeQL データベースの作成

```bash
# 特定のリポジトリの CodeQL DB を作成
mb-scanner codeql create-db <owner/repo>

# 例: facebook/react の DB を作成
mb-scanner codeql create-db facebook/react
```

### その他のコマンド

利用可能なコマンドとオプションの詳細については、ヘルプを参照してください：

```bash
# 全体のヘルプ
mb-scanner --help

# 各コマンドのヘルプ
mb-scanner search --help
mb-scanner codeql --help
mb-scanner github --help
mb-scanner visualize --help
```

## プロジェクト構造

```
mb_scanner/
├── cli/                    # CLI コマンド
│   ├── search.py          # リポジトリ検索コマンド
│   ├── codeql.py          # CodeQL 関連コマンド
│   ├── github.py          # GitHub 関連コマンド
│   ├── visualize.py       # 可視化コマンド
│   ├── count_lines.py     # 行数カウントコマンド
│   └── migrate.py         # マイグレーションコマンド
├── core/                   # 設定・ロギング
│   ├── config.py          # 環境変数と設定管理
│   └── logging_config.py  # ログ設定
├── db/                     # データベース層
│   ├── base.py            # ベースクラス
│   ├── session.py         # セッション管理
│   └── migrations.py      # マイグレーション
├── lib/                    # 外部サービス連携
│   ├── codeql/            # CodeQL CLI 連携
│   │   ├── command.py     # CodeQL コマンド実行
│   │   ├── database.py    # DB 作成・管理
│   │   ├── analyzer.py    # クエリ実行と分析
│   │   └── sarif.py       # SARIF 解析
│   ├── github/            # GitHub API クライアント
│   │   ├── client.py      # API クライアント
│   │   ├── search.py      # リポジトリ検索
│   │   └── clone.py       # リポジトリクローン
│   ├── code_counter/      # コード行数カウント
│   │   └── js_counter.py  # JavaScript 行数カウント
│   └── visualization/     # データ可視化
│       ├── scatter_plot.py # 散布図生成
│       └── boxplot.py     # 箱ひげ図生成
├── models/                # データモデル
│   └── project.py         # プロジェクトモデル
├── services/              # ビジネスロジック
│   ├── project_service.py         # プロジェクト管理
│   ├── project_search_service.py  # プロジェクト検索
│   ├── topic_service.py           # トピック管理
│   └── visualization_service.py   # 可視化サービス
├── utils/                 # 共通ユーティリティ
│   └── cleanup.py         # クリーンアップ処理
└── workflows/             # 複合処理フロー
    ├── search_and_store.py            # 検索・保存ワークフロー
    ├── codeql_database_creation.py   # CodeQL DB 作成ワークフロー
    └── codeql_query_execution.py     # CodeQL クエリ実行ワークフロー

data/                       # データ保存ディレクトリ
├── mb_scanner.db          # SQLite データベース
├── codeql-dbs/            # CodeQL データベース保存先
└── repositories/          # クローンしたリポジトリ

outputs/                    # 実行結果出力ディレクトリ
├── queries/               # CodeQL クエリ結果 (SARIF)
├── extracted_code/        # 検出されたコードの抽出結果
└── plots/                 # 可視化グラフ (PNG)
```

## 開発

### コード品質チェック

```bash
# テストの実行
pytest

# コードフォーマットと lint
just fix

# 型チェック
just typecheck
```
