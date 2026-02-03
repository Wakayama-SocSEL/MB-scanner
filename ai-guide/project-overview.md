# プロジェクト概要

## MB-Scanner とは

MB-Scanner は、GitHub 上の多数の公開 JavaScript リポジトリに対して、任意の CodeQL クエリを体系的かつ自動的に実行するためのバッチプラットフォームです。MB-search が生成したクエリや手動で作成したクエリの有効性を、実世界のコードベースで検証し、定量・定性的なデータを収集します。

## 背景と目的

### 背景
- コード品質・セキュリティ解析ツールの精度検証には、実世界の大規模コードベースでのテストが不可欠
- 個別にリポジトリを検索、クローン、解析する手作業は非効率的で再現性に欠ける
- 研究用途では、一貫した条件下での大量解析とデータ蓄積が求められる

### 目的
1. **クエリの実用性検証**: MB-search が生成した CodeQL クエリの有効性を実世界のコードベースで検証し、フィードバックループを構築する
2. **データセット構築**: コード品質・セキュリティに関する研究向けの定量・定性的なデータセットを蓄積する
3. **自動化とスケーラビリティ**: 検索からクエリ実行まで一貫した自動化により、大規模解析を実現する
4. **再現性の確保**: 同一条件での解析を繰り返し実行可能にし、研究結果の再現性を担保する

## 主な機能

### 1. 柔軟なターゲット検索
GitHub API と連携し、以下の豊富な条件を組み合わせて解析対象リポジトリを検索:
- **言語**: JavaScript
- **スター数**: 最小スター数による品質フィルタリング
- **最終更新日**: アクティブなプロジェクトに絞り込み
- **トピック**: 特定の技術領域やフレームワークに限定

### 2. データ保存・管理機能
- **SQLite + SQLAlchemy**: 検索結果を正規化された DB に保存
- **重複排除**: 同一リポジトリの重複取得を自動防止
- **メタデータ管理**: スター数、最終コミット日、言語、トピックなどを構造化して保存
- **データ鮮度管理**: `fetched_at` により取得時刻を記録し、更新判断を支援

### 3. CodeQL 実行・連携機能
- **DB 自動作成**: リポジトリクローン → CodeQL DB 作成を自動化
- **バッチクエリ実行**: 複数プロジェクトに対して複数クエリを一括実行
- **SARIF 形式出力**: 標準フォーマットで結果を保存し、他ツールとの連携を容易に
- **並列実行最適化**: スレッド数・メモリ指定でパフォーマンスチューニング可能

### 4. 可視化・分析機能
- **散布図生成**: スター数と検出結果の相関分析
- **箱ひげ図生成**: クエリ別の検出結果分布の比較
- **ベンチマーク機能**: 複数クエリの性能・有効性を定量評価

### 5. ベンチマーク機能
- **クエリ性能評価**: 複数クエリの実行時間・検出件数を比較
- **結果データ蓄積**: ベンチマーク結果を JSON 形式で保存し、後続分析を支援
- **統計的分析**: 検出パターンの傾向分析やクエリ品質評価

## アーキテクチャ概要

MB-Scanner は、Clean Architecture の原則に基づいた階層化アーキテクチャを採用しています。

```
┌─────────────────────────────────────────┐
│         CLI Layer (Typer)               │  コマンドラインインターフェース
├─────────────────────────────────────────┤
│      Workflows Layer                    │  複合処理フロー
│  - SearchAndStoreWorkflow               │
│  - CodeQLDatabaseCreationWorkflow       │
│  - CodeQLQueryExecutionWorkflow         │
├─────────────────────────────────────────┤
│      Services Layer                     │  ビジネスロジック
│  - ProjectService                       │
│  - TopicService                         │
│  - ProjectSearchService                 │
│  - VisualizationService                 │
├─────────────────────────────────────────┤
│      Library Layer                      │  外部サービス連携
│  - GitHub (client, search, clone)       │
│  - CodeQL (command, database, analyzer) │
│  - Visualization (plots)                │
│  - CodeCounter                          │
├─────────────────────────────────────────┤
│      Data Access Layer                  │  データ永続化
│  - Models (SQLAlchemy)                  │
│  - DB Session Management                │
├─────────────────────────────────────────┤
│      Core Layer                         │  共通基盤
│  - Config (Settings)                    │
│  - Logging                              │
└─────────────────────────────────────────┘
```

### レイヤー間の依存関係
- 上位レイヤーは下位レイヤーに依存可能、逆は不可（依存性逆転の原則）
- Services は Library と Models に依存
- Workflows は Services と Library を組み合わせて複合処理を実現
- CLI は Workflows を呼び出し、ユーザーとのインタラクションを担当

## 主要コンポーネント

### CLI Layer (`mb_scanner/cli/`)
ユーザーインターフェースを提供。Typer を使用した CLI コマンド群。

**コマンド名**: `mb-scanner`（正式名称）と`mbs`（短縮エイリアス）の両方を提供。

- **search.py**: リポジトリ検索・保存コマンド
- **codeql.py**: CodeQL DB 作成・クエリ実行コマンド
- **github.py**: GitHub 情報取得コマンド
- **visualize.py**: 可視化コマンド
- **benchmark.py**: ベンチマーク実行コマンド
- **count_lines.py**: JavaScript 行数カウントコマンド
- **migrate.py**: DB マイグレーションコマンド

### Workflows Layer (`mb_scanner/workflows/`)
複数のサービス・ライブラリを組み合わせた複合処理フロー。

- **SearchAndStoreWorkflow**: GitHub 検索 → DB 保存のフロー
- **CodeQLDatabaseCreationWorkflow**: リポジトリクローン → CodeQL DB 作成のフロー
- **CodeQLQueryExecutionWorkflow**: クエリ実行 → 結果分析のフロー

### Services Layer (`mb_scanner/services/`)
ビジネスロジックを提供。単一責任の原則に基づく。

- **ProjectService**: Project テーブルの CRUD 操作
- **TopicService**: Topic テーブルの操作
- **ProjectSearchService**: DB 内のプロジェクト検索・フィルタリング
- **VisualizationService**: 可視化データの準備・集計

### Library Layer (`mb_scanner/lib/`)
外部サービスやツールとの連携を抽象化。

#### GitHub (`lib/github/`)
- **GitHubClient**: GitHub API v3 クライアント（PyGithub ラッパー）
- **SearchCriteria**: 検索条件のデータクラス
- **RepositoryCloner**: git clone の実行管理

#### CodeQL (`lib/codeql/`)
- **CodeQLCLI**: CodeQL コマンドライン実行のラッパー
- **CodeQLDatabaseManager**: DB の作成・管理
- **CodeQLResultAnalyzer**: SARIF 結果の解析・カウント

#### Visualization (`lib/visualization/`)
- **ScatterPlot**: 散布図生成（matplotlib）
- **Boxplot**: 箱ひげ図生成（matplotlib）

#### CodeCounter (`lib/code_counter/`)
- **JSCounter**: JavaScript ファイルの行数カウント

### Data Access Layer (`mb_scanner/db/`, `mb_scanner/models/`)
データ永続化とモデル定義。

- **Base**: SQLAlchemy の DeclarativeBase
- **Session Management**: SessionLocal、get_db、init_db
- **Models**: Project, Topic, ProjectTopic（多対多リレーション）

詳細は [db-design.md](./db-design.md) を参照。

### Core Layer (`mb_scanner/core/`)
共通基盤。

- **Settings**: pydantic-settings による環境変数管理
- **LoggingConfig**: ロギング設定

## 技術スタック

| カテゴリ | 技術 | 理由 |
| --- | --- | --- |
| 言語 | Python 3.13+ | ライブラリが豊富で、外部コマンド連携が容易 |
| データベース | SQLite | サーバーレスでバッチ処理の進捗管理と再開が簡単 |
| ORM | SQLAlchemy | SQL を直接書かずに安全で保守しやすいコードを実現 |
| CLI | Typer | 型安全で可読性の高い CLI 構築 |
| GitHub API | PyGithub | 条件に合うリポジトリを効率よく取得 |
| CodeQL | CodeQL CLI | 静的解析クエリの実行とデータベース管理 |
| 可視化 | Matplotlib | 散布図・箱ひげ図などのグラフ生成 |
| 数値計算 | NumPy, SciPy | 統計処理と数値計算 |
| 外部コマンド実行 | subprocess | git clone や codeql コマンドを柔軟に呼び出す |
| 開発支援 | uv, just, pytest, ruff, pyright | パッケージ管理、タスク運用、テスト、品質チェックを統一 |

## ディレクトリ構造

```
mb_scanner/
├── cli/                    # CLI コマンド
│   ├── search.py          # リポジトリ検索コマンド
│   ├── codeql.py          # CodeQL 関連コマンド
│   ├── github.py          # GitHub 関連コマンド
│   ├── visualize.py       # 可視化コマンド
│   ├── count_lines.py     # 行数カウントコマンド
│   ├── benchmark.py       # ベンチマークコマンド
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
│   │   ├── clone.py       # リポジトリクローン
│   │   └── schema.py      # データスキーマ
│   ├── code_counter/      # コード行数カウント
│   │   └── js_counter.py  # JavaScript 行数カウント
│   └── visualization/     # データ可視化
│       ├── scatter_plot.py # 散布図生成
│       └── boxplot.py     # 箱ひげ図生成
├── models/                # データモデル
│   ├── project.py         # Project, Topic, ProjectTopic
│   ├── extraction.py      # 抽出結果モデル
│   ├── summary.py         # サマリーモデル
│   ├── sarif.py           # SARIF フォーマットモデル
│   └── benchmark.py       # ベンチマーク結果モデル
├── services/              # ビジネスロジック
│   ├── project_service.py         # プロジェクト管理
│   ├── project_search_service.py  # プロジェクト検索
│   ├── topic_service.py           # トピック管理
│   ├── visualization_service.py   # 可視化サービス
│   └── benchmark_runner.py        # ベンチマーク実行
├── utils/                 # 共通ユーティリティ
│   └── cleanup.py         # クリーンアップ処理
└── workflows/             # 複合処理フロー
    ├── search_and_store.py            # 検索・保存ワークフロー
    ├── codeql_database_creation.py   # CodeQL DB 作成ワークフロー
    └── codeql_query_execution.py     # CodeQL クエリ実行ワークフロー

data/                       # データ保存ディレクトリ
├── mb_scanner.db          # SQLite データベース
├── codeql-dbs/            # CodeQL データベース保存先
├── repositories/          # クローンしたリポジトリ
└── benchmarks/            # ベンチマーク結果

outputs/                    # 実行結果出力ディレクトリ
├── queries/               # CodeQL クエリ結果 (SARIF)
├── extracted_code/        # 検出されたコードの抽出結果
└── plots/                 # 可視化グラフ (PNG)
```

## データフロー

### 典型的な実行フロー

#### 1. リポジトリ検索・保存フロー
```
User Command (mbs search)
  ↓
CLI (search.py)
  ↓
SearchAndStoreWorkflow
  ↓
GitHubClient.search_repositories()  →  GitHub API
  ↓
ProjectService.save_project()
  ↓
SQLite DB (projects, topics, project_topics)
```

#### 2. CodeQL データベース作成フロー
```
User Command (mbs codeql create-db)
  ↓
CLI (codeql.py)
  ↓
CodeQLDatabaseCreationWorkflow
  ↓
RepositoryCloner.clone()  →  git clone
  ↓
CodeQLDatabaseManager.create_database()  →  codeql database create
  ↓
data/codeql-dbs/{project-name}/
```

#### 3. CodeQL クエリ実行フロー
```
User Command (mbs codeql query)
  ↓
CLI (codeql.py)
  ↓
CodeQLQueryExecutionWorkflow
  ↓
CodeQLCLI.analyze_database()  →  codeql database analyze
  ↓
CodeQLResultAnalyzer.count_results()
  ↓
outputs/queries/{query-name}/{project-name}.sarif
```

#### 4. 可視化フロー
```
User Command (mbs visualize scatter)
  ↓
CLI (visualize.py)
  ↓
VisualizationService.prepare_scatter_data()
  ↓
SQLite DB (projects, SARIF 結果)
  ↓
ScatterPlot.create()  →  matplotlib
  ↓
outputs/plots/{plot-name}.png
```

## 設計判断のポイント

### なぜ SQLite を採用したか
- **サーバーレス**: 外部 DB サーバー不要で環境構築が簡単
- **ポータブル**: ファイル 1 つでデータ移行が容易
- **バッチ処理に最適**: 大量書き込みのトランザクション管理が効率的
- **進捗管理**: 中断・再開が容易で、冪等性のある処理設計に適合

### なぜ階層化アーキテクチャか
- **責任分離**: 各層が単一の責任を持ち、変更の影響範囲を局所化
- **テスタビリティ**: 各層を独立してテスト可能
- **拡張性**: 新機能追加時に既存コードへの影響を最小化
- **再利用性**: Services や Library は複数の CLI コマンドから再利用可能

### なぜ Workflow を分離したか
- **複雑性の管理**: 複数サービスを組み合わせる処理をワークフローとして抽出
- **トランザクション管理**: DB セッションとエラーハンドリングを一箇所に集約
- **CLI のシンプル化**: CLI は引数解析とワークフロー呼び出しに専念

## 拡張ポイント

### 新しい CLI コマンドを追加する場合
1. `mb_scanner/cli/` に新しいファイルを作成
2. Typer を使ってコマンド定義
3. 必要に応じて新しい Workflow を作成
4. `mb_scanner/cli/__init__.py` に登録

### 新しい検索条件を追加する場合
1. `mb_scanner/lib/github/schema.py` の `SearchCriteria` に追加
2. `mb_scanner/lib/github/search.py` で条件を GitHub API クエリに変換
3. `mb_scanner/cli/search.py` でオプションとして公開

### 新しい可視化を追加する場合
1. `mb_scanner/lib/visualization/` に新しいプロット生成モジュールを作成
2. `mb_scanner/services/visualization_service.py` にデータ準備ロジックを追加
3. `mb_scanner/cli/visualize.py` に新しいサブコマンドを追加

### データベーススキーマを変更する場合
1. `mb_scanner/models/` でモデルを変更
2. `mb_scanner/db/migrations.py` にマイグレーション処理を追加
3. `mb-scanner migrate` コマンドで既存 DB を更新

## パフォーマンス考慮事項

### 並列処理
- CodeQL DB 作成・クエリ実行は時間がかかるため、バッチ処理の並列化が推奨される
- 現在は逐次実行だが、将来的に `joblib` や `multiprocessing` での並列化を検討

### メモリ管理
- 大量のリポジトリを処理する際は、DB セッションのライフサイクル管理が重要
- Workflow ごとにセッションを開閉し、メモリリークを防止

### ディスク容量
- CodeQL DB はリポジトリサイズの数倍のディスク容量を消費
- 定期的なクリーンアップ処理（`utils/cleanup.py`）の実装を推奨

## 関連ドキュメント

- [db-design.md](./db-design.md) - データベース設計の詳細
- [testing-guidelines.md](./testing-guidelines.md) - テストガイドライン
- [development-setup.md](./development-setup.md) - 開発環境セットアップ
- [coding-guidelines.md](./coding-guidelines.md) - コーディング規約と型定義ガイドライン

## まとめ

MB-Scanner は、GitHub リポジトリの検索から CodeQL 解析、結果の可視化までを統合したプラットフォームです。階層化アーキテクチャにより、各コンポーネントが独立して拡張可能であり、研究用途での大規模解析に必要な再現性とスケーラビリティを備えています。
