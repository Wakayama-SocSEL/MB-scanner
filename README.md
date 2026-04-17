# MB-Scanner

MB-Scanner は、GitHub 上の多数の公開 JavaScript リポジトリに対して、任意の CodeQL クエリを体系的かつ自動的に実行するためのバッチプラットフォームです。MB-search が生成したクエリや手動で作成したクエリの有効性を、実世界のコードベースで検証し、定量・定性的なデータを収集します。

## 目的
- MB-search が生成した CodeQL クエリの実用性を検証し、フィードバックループを構築する。
- コード品質・セキュリティに関する研究向けのデータセットを蓄積する。

## 技術スタック
| カテゴリ | 技術 | 理由 |
| --- | --- | --- |
| 言語 | Python 3.13+ | ライブラリが豊富で、外部コマンド連携が容易。 |
| アーキテクチャ | Clean Architecture | 依存方向の厳守によりテスタビリティと保守性を確保。 |
| データベース | SQLite | サーバーレスでバッチ処理の進捗管理と再開が簡単。 |
| ORM | SQLAlchemy | SQL を直接書かずに安全で保守しやすいコードを実現。 |
| GitHub API | `PyGithub` | 条件に合うリポジトリを効率よく取得。 |
| 外部ツール実行 | `subprocess` | `git clone` や `codeql` コマンドを柔軟に呼び出す。 |
| ツール管理 | `mise` | uv / node / pnpm のバージョンを `.mise.toml` で一元管理。 |
| パッケージ管理 | `uv` | Python ランタイムと依存を高速にインストール・ロック。 |

## 前提条件

**必要なのは mise だけ** です。uv / node / pnpm は mise が `.mise.toml` から自動でインストールします。

```bash
# mise のインストール（未導入の場合）
curl https://mise.run | sh

# mise を有効化（シェルに合わせて）
eval "$(~/.local/bin/mise activate bash)"   # or zsh / fish
```

Docker で使う場合は mise すら不要です（コンテナが全部持っている）。

## セットアップ

### ローカル（ネイティブ）

```bash
# リポジトリのクローン
git clone https://github.com/Wakayama-SocSEL/MB-Scanner.git
cd MB-Scanner

# ツール（uv / node / pnpm）を .mise.toml から自動インストール
mise install

# Python 仮想環境の作成と依存関係のインストール
mise run python-deps
```

### Docker（推奨: サーバ環境）

**日常開発・実行は `dev` コンテナを使います**。ソースがホストから bind mount されているので、編集はホストのエディタで行い、実行だけコンテナ内で行います。

```bash
# dev イメージをビルド（初回のみ。CodeQL のダウンロードで数分かかる）
mise run docker:build

# dev コンテナを起動
mise run docker:up

# シェルに入る
mise run docker:shell

# --- 以下はコンテナ内 ---
mise install           # uv / node / pnpm を .mise.toml から入れる
mise run python-deps   # Python 仮想環境 + 依存関係

# これで準備完了。以降は編集 → 即実行できる
mbs search
mbs codeql create-db facebook/react
mise run test
```

コンテナから抜けたあとも再度 `mise run docker:shell` で入り直せます。停止するには:

```bash
mise run docker:down
```

### 環境変数の設定

MB-Scanner を使用するには、GitHub API トークンが必要です。

```bash
cp .env.sample .env
```

`.env` ファイルを開き、GitHub API トークンを設定します:

```bash
GITHUB_TOKEN="your_github_token_here"
```

GitHub Personal Access Token は [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) から取得できます（`public_repo` スコープが必要）。

## 基本的な使い方

```bash
# リポジトリの検索と保存
mbs search

# CodeQL データベースの作成
mbs codeql create-db facebook/react

# ヘルプ
mbs --help
mbs search --help
mbs codeql --help
```

## 再現実験（論文提出時など）

**`archive` プロファイル**を使うと、依存も venv もイメージに焼き込まれた **再現可能な固定イメージ**をビルドできます。日常起動はしません。

```bash
# 再現実験用イメージをビルド（稀にしか実行しない）
mise run docker:archive:build

# 固定イメージでコマンドを実行
mise run docker:archive:run -- mbs search
mise run docker:archive:run -- mbs codeql create-db facebook/react

# 論文用に特定バージョンで凍結
docker tag mb_scanner-archive:latest mb_scanner:2026-04-paper-experiment
docker save mb_scanner:2026-04-paper-experiment -o archive.tar
```

再現実験イメージ (`Dockerfile.prod`) は `final` ステージに Python venv + CodeQL + Node.js ランタイムしか含まず、**uv も mise も含みません**。イメージサイズが最小化されています。

## 開発

### よく使うコマンド

```bash
# 全チェック一括実行（Lint + 型チェック + テスト + アーキテクチャ検証）
mise run check

# 個別実行
mise run test              # テスト
mise run lint              # Lint
mise run typecheck         # 型チェック
mise run check-arch        # アーキテクチャ検証（import-linter）

# コードフォーマット + 自動修正
mise run fix
```

### Docker タスク一覧

```bash
# 日常開発用（dev）
mise run docker:build       # dev イメージをビルド
mise run docker:up          # dev コンテナを起動
mise run docker:shell       # シェルに入る
mise run docker:logs        # ログ表示
mise run docker:down        # 停止
mise run docker:restart     # 再起動

# 再現実験用（archive / prod）
mise run docker:archive:build     # prod イメージをビルド
mise run docker:archive:run       # prod イメージでコマンド実行
```

全タスク一覧: `mise tasks`

## プロジェクト構造

```
mb_scanner/
├── domain/                   # ドメインモデル + ポート（Protocol）
│   ├── entities/             # Pydantic BaseModel（Project, SARIF, Benchmark等）
│   └── ports/                # インターフェース定義
├── use_cases/                # ビジネスロジック（検索, 解析, ベンチマーク）
├── adapters/                 # 外部接続
│   ├── cli/                  # Typer CLI（composition root）
│   ├── repositories/         # SQLAlchemy Repository 実装
│   └── gateways/             # 外部サービス連携（GitHub, CodeQL, 可視化）
└── infrastructure/           # フレームワーク（ORM, DB接続, 設定）

mb-analyzer-legacy/           # [DEPRECATED] 旧 TypeScript analyzer monorepo (pnpm workspace)
├── apps/
│   └── equivalence-runner/   # 旧 equivalence-check コマンドが依存する CLI
└── features/                 # Package by Feature + 内部に Clean Architecture 4 層
    ├── equivalence-check/    # 旧 slow/fast 等価性チェック（後継: mb-analyzer/equivalence-checker）
    ├── pattern-mining/       # 旧スケルトン
    └── rule-codegen/         # 旧スケルトン
# mb-analyzer/ は新 single-package 構成で再構築予定（equivalence-checker / pruning / 他）
codeql/                       # CodeQL クエリ設定
data/                         # ランタイムデータ（DB, クローン, CodeQL DB）
outputs/                      # クエリ結果・可視化出力
tests/                        # テスト（CA 構造をミラー）

Dockerfile.dev                # 日常開発用（1 ステージ）
Dockerfile.prod               # 再現実験用（multi-stage 最適化）
docker-compose.yml            # dev サービス + scanner (archive profile)
.mise.toml                    # ツールバージョン + タスク定義（唯一の真実の源泉）
```
