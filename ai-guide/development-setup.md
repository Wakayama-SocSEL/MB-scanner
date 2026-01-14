# 開発環境セットアップ

## 前提条件

### 必要なソフトウェア
| カテゴリ | 技術 | 理由 |
| --- | --- | --- |
| 言語 | Python 3.13+ | ライブラリが豊富で、外部コマンド連携が容易。 |
| データベース | SQLite | サーバーレスでバッチ処理の進捗管理と再開が簡単。 |
| ORM | SQLAlchemy | SQL を直接書かずに安全で保守しやすいコードを実現。 |
| GitHub API | `PyGithub` | 条件に合うリポジトリを効率よく取得。 |
| 外部ツール実行 | `subprocess` | `git clone` や `codeql` コマンドを柔軟に呼び出す。 |
| 開発支援 | `uv`, `just`, `git` | パッケージ管理とタスク運用など。 |

### 推奨ツール
- **VS Code**: 推奨エディタ
- **ruff拡張機能** コードフォーマット・リント

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/Wakayama-SocSEL/MB-scanner.git
cd MB-scanner
```

### 2. 依存関係のインストール
```bash
just python-deps
```

### 3. 環境変数の設定

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


### 基本的なコマンド

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
## 開発用コマンド

### コード品質チェック

```bash
# テストの実行
uv run pytest

# コードフォーマットと lint
just fix

# 型チェック
just typecheck
```

## 開発環境の構成

### ディレクトリ構造

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

### 開発フロー
2. テストを作成
3. コードを実装
4. テスト・リント・型チェックを実行

## トラブルシューティング

### よくある問題と解決方法

## 開発のベストプラクティス

### 1. コード規約
- ruffの設定に従う（自動フォーマット）
- TypeScriptの厳格モードを維持
- 意味のある変数名・関数名を使用

## 便利な開発ツール

### VS Code拡張機能
- **ruff**: コードフォーマット・リント
