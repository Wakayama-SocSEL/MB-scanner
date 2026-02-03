# システム設計とアーキテクチャ

## プロジェクト概要
MB-Scannerは、GitHub上の多数のJavaScriptリポジトリに対してCodeQLクエリを体系的に実行するためのバッチプラットフォームです。
定量・定性的なデータセットを構築し、クエリの有効性を実世界のコードベースで検証することを目的としています。

## アーキテクチャ設計
本プロジェクトは **Clean Architecture** の原則に基づいた階層化アーキテクチャを採用しています。

### レイヤー構造と依存関係
依存性逆転の原則に従い、上位レイヤーは下位レイヤーに依存しますが、逆は不可とします。

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

### ディレクトリ構造 (File Map)
AIエージェントはこのマップを参照してファイルの配置場所を特定すること。

```text
mb_scanner/
├── cli/                    # CLI コマンド (Entry Points)
│   ├── search.py          # リポジトリ検索
│   ├── codeql.py          # CodeQL DB作成・クエリ実行
│   ├── visualize.py       # 可視化
│   └── migrate.py         # DBマイグレーション
├── workflows/             # 複合処理フロー (Transaction Boundary)
│   ├── search_and_store.py
│   ├── codeql_database_creation.py
│   └── codeql_query_execution.py
├── services/              # ビジネスロジック
│   ├── project_service.py
│   └── visualization_service.py
├── lib/                    # 外部連携アダプタ
│   ├── codeql/            # CodeQL CLI wrapper
│   ├── github/            # GitHub API client (PyGithub)
│   └── visualization/     # グラフ描画 (Matplotlib)
├── db/                     # DB接続・セッション管理
├── models/                # SQLAlchemyモデル定義
│   ├── project.py         # Project, Topic
│   └── sarif.py           # 解析結果モデル
└── core/                   # 設定・ロギング
    └── config.py          # Pydantic Settings
```

### データフロー
典型的な処理は以下のパイプラインで実行されます。
1. **検索・保存**: GitHub API検索 -> 重複排除 -> DB保存 (`SearchAndStoreWorkflow)
2. **解析準備**: リポジトリClone -> CodeQL DB作成 (CodeQLDatabaseCreationWorkflow)
3. **クエリ実行**: クエリ実行 -> SARIF解析 -> 結果保存 (CodeQLQueryExecutionWorkflow)
4. **可視化**: DB集計 -> グラフ生成 (VisualizationService)

## 技術スタックと選定理由
- **SQLite**: サーバーレスで管理が容易。バッチ処理のトランザクション管理に最適。
- **SQLAlchemy**: SQLを直接書かずに安全なコードを実現するため。
- **Typer**: 型安全で可読性の高いCLIを構築するため。
- **PyGithub**: リポジトリ検索の効率化。

## 設計判断のポイント
- **SQLiteの採用**: 外部サーバー不要でポータブル。中断・再開が必要なバッチ処理の進捗管理に適しているため。
- **Workflow層の分離**: 複雑な依存関係をCLIやServiceから切り離し、トランザクション管理を一箇所に集約するため。
