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

`.env` ファイルを開き、以下の設定を行います：

#### 必須設定

```bash
# GitHub API Token（必須）
GITHUB_TOKEN="your_github_token_here"
```

GitHub Personal Access Token は以下の手順で取得できます：
1. GitHub の [Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens) にアクセス
2. "Generate new token" をクリック
3. スコープで `public_repo` を選択（公開リポジトリへの読み取りアクセス）
4. 生成されたトークンを `.env` ファイルの `GITHUB_TOKEN` に設定

#### オプション設定

以下の設定は任意です。必要に応じてコメントを外して設定してください：

```bash
# データディレクトリとDBファイルのパス
# MB_SCANNER_DATA_DIR="/path/to/your/data/"
# MB_SCANNER_DB_FILE="/path/to/your/mb_scanner.db"

# ログ設定
# MB_SCANNER_LOG_LEVEL="INFO"
# MB_SCANNER_LOG_FILE="/path/to/your/logs/mb_scanner.log"
# MB_SCANNER_LOG_TO_CONSOLE=true

# GitHub検索のデフォルト条件
# MB_SCANNER_GITHUB_SEARCH_DEFAULT_LANGUAGE="JavaScript"
# MB_SCANNER_GITHUB_SEARCH_DEFAULT_MIN_STARS=100
# MB_SCANNER_GITHUB_SEARCH_DEFAULT_MAX_DAYS_SINCE_COMMIT=365

# CodeQL関連設定
# MB_SCANNER_CODEQL_CLI_PATH="codeql"
# MB_SCANNER_CODEQL_DB_BASE_DIR="/path/to/codeql-dbs"
# MB_SCANNER_CODEQL_CLONE_BASE_DIR="/tmp/mb-scanner-clones"
# MB_SCANNER_CODEQL_DEFAULT_LANGUAGE="javascript"
```

## 使い方

### GitHub リポジトリの検索と保存

`mb-scanner search` コマンドを使用して、指定した条件で GitHub リポジトリを検索し、データベースに保存します。

```bash
# デフォルト設定で実行（JavaScript, 100+ stars, 365日以内の更新）
mb-scanner search

# または明示的に search コマンドを指定
mb-scanner search
```

### コマンドラインオプション

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--language` | `-l` | `JavaScript` | 検索対象の主要言語 |
| `--min-stars` | `-s` | `100` | 最小スター数 |
| `--max-days-since-commit` | `-d` | `365` | 最終コミットからの最大経過日数 |
| `--max-results` | `-n` | なし | 取得する最大リポジトリ数（指定しない場合は全件） |
| `--update` | `-u` | `False` | 既存プロジェクトを更新する |

### 使用例

```bash
# Python リポジトリで 1000+ stars、180日以内の更新、最大50件取得
mb-scanner search --language Python --min-stars 1000 --max-days-since-commit 180 --max-results 50

# 短縮オプションを使用
mb-scanner search -l TypeScript -s 500 -d 90 -n 25

# 既存プロジェクトの更新モードで実行
mb-scanner search -l JavaScript -s 100 -u

# ヘルプの表示
mb-scanner --help
mb-scanner search --help
```

### 実行結果

コマンド実行後、以下の統計情報が表示されます：

```
検索結果:
  検索結果総数: 50
  新規保存: 45
  更新: 3
  スキップ: 2
  失敗: 0
```

データは `data/mb_scanner.db` (SQLite) に保存されます。

### CodeQL データベースの作成

保存したリポジトリに対して CodeQL データベースを作成できます。

#### 前提条件

CodeQL CLI のインストールが必要です：

1. [CodeQL CLI のダウンロードページ](https://github.com/github/codeql-cli-binaries/releases) から最新版をダウンロード
2. 解凍して PATH に追加、または `MB_SCANNER_CODEQL_CLI_PATH` 環境変数で指定

```bash
# インストール確認
codeql --version
```

#### 単一プロジェクトの DB 作成

特定のプロジェクトに対して CodeQL データベースを作成します。

```bash
# 基本的な使い方
mb-scanner codeql create-db <owner/repo>

# 例: facebook/react の DB を作成
mb-scanner codeql create-db facebook/react

# 言語を指定して作成
mb-scanner codeql create-db facebook/react --language javascript

# 既存の DB を上書き
mb-scanner codeql create-db facebook/react --force
```

#### バッチ処理（全プロジェクトの DB 作成）

データベース上の全プロジェクトに対して一括で CodeQL データベースを作成します。

```bash
# すべてのプロジェクトに対して DB を作成
mb-scanner codeql create-db-batch

# 最大 10 件のプロジェクトに対して作成
mb-scanner codeql create-db-batch --max-projects 10

# 言語を指定
mb-scanner codeql create-db-batch --language javascript

# 既存の DB を上書き
mb-scanner codeql create-db-batch --force
```

#### コマンドラインオプション

**create-db コマンド:**

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--language` | - | `javascript` | 解析言語（javascript, python, など） |
| `--force` | `-f` | `False` | 既存 DB を上書きする |

**create-db-batch コマンド:**

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| `--language` | - | `javascript` | 解析言語 |
| `--max-projects` | - | なし | 最大プロジェクト数（指定しない場合は全件） |
| `--skip-existing` | - | `True` | 既存 DB をスキップする |
| `--force` | `-f` | `False` | 既存 DB を上書きする |

#### DB の保存先

作成された CodeQL データベースは以下の場所に保存されます：

```
data/codeql-dbs/
├── facebook-react/        # facebook/react の DB
├── microsoft-typescript/  # microsoft/typescript の DB
└── ...
```

一時的にクローンされたリポジトリは `/tmp/mb-scanner-clones/` に保存され、DB 作成後に自動的に削除されます。

#### 実行結果

バッチ処理実行後、以下の統計情報が表示されます：

```
=== Batch Creation Summary ===
Total: 50
✓ Created: 45
⊘ Skipped: 3
✗ Failed: 2
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

### プロジェクト構造

```
mb_scanner/
├── cli/                    # CLI コマンド
│   ├── __init__.py        # Typer アプリ統合
│   ├── search.py          # search コマンド
│   └── codeql.py          # codeql コマンド
├── core/                   # 設定・ロギング
├── db/                     # データベース（モデル、セッション）
├── lib/                    # 外部サービス連携
│   ├── codeql/            # CodeQL CLI 連携
│   │   ├── command.py     # CodeQL コマンド実行
│   │   └── database.py    # DB 管理
│   └── github/            # GitHub API クライアント
│       ├── client.py      # API クライアント
│       ├── clone.py       # リポジトリクローン
│       └── search.py      # 検索ロジック
├── services/              # ビジネスロジック
├── utils/                 # 共通ユーティリティ
└── workflows/             # 複合処理フロー
    ├── search_and_store.py          # 検索・保存ワークフロー
    └── codeql_database_creation.py  # CodeQL DB 作成ワークフロー
```
