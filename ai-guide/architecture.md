# アーキテクチャ・設計ガイド

## プロジェクト概要

MB-Scannerは、GitHub上の多数のJavaScriptリポジトリに対してCodeQLクエリを体系的に実行するためのバッチプラットフォームです。定量・定性的なデータセットを構築し、クエリの有効性を実世界のコードベースで検証することを目的としています。

---

## アーキテクチャ設計

**Clean Architecture** の原則に基づいた階層化アーキテクチャを採用しています。依存の方向は `CLI -> Workflows -> Services -> Library/Models` を厳守すること。

### レイヤー構造

1. **CLI Layer** (`mb_scanner/cli/`)
   - ユーザーインターフェースを担当。Typerを使用。
   - Workflowsを呼び出し、引数解析と表示を行う。
2. **Workflows Layer** (`mb_scanner/workflows/`)
   - 複数のServicesやLibraryを組み合わせた複合処理フロー。
   - トランザクション管理とエラーハンドリングを集約する。
3. **Services Layer** (`mb_scanner/services/`)
   - ビジネスロジック（CRUD操作、検索、集計）を提供。単一責任の原則に基づく。
4. **Library Layer** (`mb_scanner/lib/`)
   - 外部ツール（GitHub API, CodeQL CLI, Matplotlib）との連携を抽象化。
5. **Data Access Layer** (`mb_scanner/db/`, `mb_scanner/models/`)
   - SQLAlchemyを使用したデータ永続化とモデル定義。

### ディレクトリ構造

```text
mb_scanner/
├── cli/                    # CLI コマンド (Entry Points)
│   ├── search.py          # リポジトリ検索
│   ├── codeql.py          # CodeQL DB作成・クエリ実行
│   ├── visualize.py       # 可視化
│   ├── benchmark.py       # ベンチマーク等価性チェック
│   └── migrate.py         # DBマイグレーション
├── workflows/             # 複合処理フロー (Transaction Boundary)
│   ├── search_and_store.py
│   ├── codeql_database_creation.py
│   └── codeql_query_execution.py
├── services/              # ビジネスロジック
│   ├── project_service.py
│   ├── visualization_service.py
│   └── benchmark_runner.py
├── lib/                   # 外部連携アダプタ
│   ├── codeql/            # CodeQL CLI wrapper
│   ├── github/            # GitHub API client (PyGithub)
│   └── visualization/     # グラフ描画 (Matplotlib)
├── resources/             # 外部実行環境用リソース
│   └── benchmark/         # ベンチマーク実行用JavaScriptファイル
│       ├── sandbox.js     # Node.js サンドボックス環境設定
│       ├── stabilizers.js # 非決定的関数の固定化
│       └── strategies/    # 比較用ルール
├── db/                    # DB接続・セッション管理
├── models/                # SQLAlchemyモデル定義
│   ├── project.py         # Project, Topic
│   ├── sarif.py           # 解析結果モデル
│   └── benchmark.py       # ベンチマーク結果モデル
└── core/                  # 設定・ロギング
    └── config.py          # Pydantic Settings
```

### データフロー

1. **検索・保存**: GitHub API検索 → 重複排除 → DB保存 (`SearchAndStoreWorkflow`)
2. **解析準備**: リポジトリClone → CodeQL DB作成 (`CodeQLDatabaseCreationWorkflow`)
3. **クエリ実行**: クエリ実行 → SARIF解析 → 結果保存 (`CodeQLQueryExecutionWorkflow`)
4. **可視化**: DB集計 → グラフ生成 (`VisualizationService`)

---

## 新機能追加ガイド

アーキテクチャのレイヤー構造（CLI -> Workflows -> Services -> Lib）を遵守すること。

### 1. 新しい CLI コマンドの追加

1. `mb_scanner/cli/` に新しいPythonファイルを作成する。
2. `Typer` を使用してコマンドと引数を定義する。
3. ビジネスロジックが複雑な場合は `mb_scanner/workflows/` に新しいWorkflowクラスを作成する。
4. `mb_scanner/cli/__init__.py` に新しいコマンドを登録する。

### 2. 新しい検索条件の追加

1. `mb_scanner/lib/github/schema.py` の `SearchCriteria` クラスにフィールドを追加する。
2. `mb_scanner/lib/github/search.py` でGitHub APIのクエリ文字列への変換ロジックを実装する。
3. `mb_scanner/cli/search.py` の引数定義を更新する。

### 3. 新しい可視化の追加

1. `mb_scanner/lib/visualization/` に新しいプロット生成モジュールを作成する。
2. `mb_scanner/services/visualization_service.py` にデータ取得・加工ロジックを追加する。
3. `mb_scanner/cli/visualize.py` に新しいサブコマンドを追加する。

### 4. データベーススキーマの変更

1. `mb_scanner/models/` 内の該当モデルクラスを変更する。
2. `mb_scanner/db/migrations.py` にマイグレーション処理（ALTER TABLE等）を追加する。
   - ※Alembicは使用していないため、手動またはスクリプトによる更新が必要。
3. `mbs migrate` コマンドで既存のデータベースを更新する。

### 5. ベンチマーク機能の拡張

ベンチマークの等価性チェック機能の拡張方法。

#### サンドボックス環境のカスタマイズ

- **安定化処理の追加**: `mb_scanner/resources/benchmark/stabilizers.js` に新しい固定化ロジックを追加する。
- **サンドボックスへの統合**: `sandbox.js` の `createSandbox` 関数で安定化処理を適用する。
- **設計原則**: 安定化ロジックは `stabilizers.js` に分離し、実行のたびに同じ結果が得られるようシード値・固定値を使用すること。

#### 比較ストラテジーのアーキテクチャ

現在の実装（2026年2月）:
- 全戦略実行: 適用可能な全ての戦略を実行し、結果を `strategy_results` 配列に格納
- stdout戦略の特別扱い: 適用可能なら他の戦略を実行せず即返し
- ステータス判定: 全て"equal"なら"equal"、1つでも"not_equal"なら"not_equal"

データフロー:
1. **Node.js側** (`runner.js`): 各戦略を実行し、結果をJSON出力
2. **Python側** (`benchmark_runner.py`): JSONをパースして `EquivalenceResult` に変換
3. **モデル**: `StrategyResult`（個別戦略）、`EquivalenceResult`（総合結果）

新しい戦略の追加手順:
1. `strategies/` に新ストラテジークラスを作成（`canApply()`, `compare()` 実装）
2. `runner.js` で戦略リストに追加
3. `models/benchmark.py` の `comparison_method` Literal に追加
4. テスト追加（`tests/services/test_benchmark_runner.py`）

---

## コーディング規約

### 型定義の原則

`Any` 型の使用は厳禁。

| ユースケース | 推奨する型 | 理由 |
| :--- | :--- | :--- |
| **外部入力の読み込み** | `Pydantic` | 厳密なバリデーションとパース機能が必要なため |
| **設定オブジェクト** | `Pydantic` | デフォルト値の管理や環境変数の読み込みのため |
| **JSON出力** | `Pydantic` | `model_dump_json()` によるシリアライズとスキーマ生成を活用するため |
| **関数の内部戻り値** | `TypedDict` | ランタイムオーバーヘッドがなく軽量なため |
| **内部データ構造** | `TypedDict` | バリデーション不要で型ヒントのみ必要な場合 |

モデルの配置ルール:
- **Pydanticモデル**: `mb_scanner/models/` に配置する。
- **TypedDict**: 原則として使用するモジュール内に定義する。複数モジュールで再利用する場合のみ `models/` へ移動する。

### ファイル形式の選択

**JSON を選択すべき場合:**
- データが階層構造を持つ場合（例: SARIF、抽出結果）
- 型情報（文字列/数値/真偽値/null）を区別して保存したい場合
- Pydanticモデルをそのままダンプしたい場合

**CSV を選択すべき場合:**
- Excelやスプレッドシートでの閲覧・分析が主目的の場合
- ネストのない単純なテーブル形式のデータ

### 静的解析ツール

- **Linter/Formatter**: `ruff`（`just fix` で実行）
- **Type Checker**: `pyright`（`just typecheck` で実行）

---

## データベース設計

### 技術スタック

- **RDBMS**: SQLite（サーバーレス、バッチ処理の進捗管理に適しているため）
- **ORM**: SQLAlchemy（宣言的マッピング）

### テーブル設計

**projects テーブル**: GitHubプロジェクト（リポジトリ）の基本情報
- `id`: PK (Integer)
- `full_name`: UNIQUE / INDEX (String)
- `stars`: INDEX (Integer)
- `last_commit_date`: INDEX (DateTime)
- `fetched_at`: データ取得時刻 (UTC) — 更新判断に使用
- `js_lines_count`: JavaScript行数

**topics テーブル**: トピックのマスタデータ
- `id`: PK
- `name`: UNIQUE / INDEX

**project_topics テーブル**: ProjectsとTopicsの多対多中間テーブル
- `project_id`: FK (CASCADE)
- `topic_id`: FK (CASCADE)
- 複合主キー: (`project_id`, `topic_id`)

### SQLAlchemy 実装詳細

- すべてのモデルは `Base` を継承し、`Base.metadata.create_all(bind=engine)` で生成する。
- リレーション: `Project.topics` / `Topic.projects`、`secondary="project_topics"`、`lazy="selectin"`（N+1回避）
- DB初期化: `mb_scanner.db.session.init_db()` を呼び出す。
- セッション: 操作時は `SessionLocal()` からサービス層（`ProjectService` など）を経由してアクセスする。
- **命名規則**: GitHubリポジトリを表す用語は `Project` を使用すること（Repositoryパターンとの混同を避けるため）。

### 運用上の注意

- `fetched_at` カラムは `datetime.now(UTC)` で自動更新し、再取得の判断基準とする。
