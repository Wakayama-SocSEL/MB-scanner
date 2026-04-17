# アーキテクチャ・設計ガイド

## プロジェクト概要

MB-Scannerは、GitHub上の多数のJavaScriptリポジトリに対してCodeQLクエリを体系的に実行するためのバッチプラットフォームです。定量・定性的なデータセットを構築し、クエリの有効性を実世界のコードベースで検証することを目的としています。

---

## アーキテクチャ設計

**実用的 Clean Architecture（Pragmatic CA）** を採用しています。依存の方向は常に内側に向かい、内側は外側を知りません。

### レイヤー構造

```
infrastructure（最外層）→ adapters → use_cases → domain（最内層）
  依存は常に内側に向かう。内側は外側を知らない。
```

1. **Domain 層** (`mb_scanner/domain/`)
   - ドメインモデル（Pydantic BaseModel）とポート（Protocol）を定義。
   - 許可する外部依存は `pydantic` のみ。`sqlalchemy`, `typer`, `github`, `matplotlib` は禁止。
2. **Use Cases 層** (`mb_scanner/use_cases/`)
   - ビジネスロジックを集約。Protocol 経由で依存注入（DI）を受ける。
   - domain にのみ依存し、具象アダプターを直接 import しない。
3. **Adapters 層** (`mb_scanner/adapters/`)
   - 入力アダプター（CLI）と出力アダプター（repositories, gateways）。
   - CLI は **composition root** として依存の組み立てを担当。
   - domain + use_cases に依存。infrastructure へのアクセスも許可（CLI での DI 組み立て、Repository での ORM 使用）。
4. **Infrastructure 層** (`mb_scanner/infrastructure/`)
   - フレームワーク・ドライバー層。ORM 定義、DB 接続、設定、ロギング。

### 依存ルールの自動検証

`import-linter` で依存方向を自動チェックしています。

```bash
mise run check-arch   # import-linter でレイヤー契約を検証
```

**契約:**
- **レイヤー契約**: infrastructure → adapters → use_cases → domain の順のみ許可
- **ドメイン禁止契約**: domain 層が `sqlalchemy`, `typer`, `github`, `matplotlib` を import していないことを保証
- **例外**: `adapters → infrastructure` は `ignore_imports` で許可（CLI=composition root, repositories=ORM 実装のため）

### ディレクトリ構造

```text
mb_scanner/
├── domain/                   # === Entities 層（最内層）===
│   ├── entities/             # Pydantic BaseModel によるドメインモデル
│   │   ├── project.py        # Project, Topic
│   │   ├── benchmark.py      # EquivalenceResult, EquivalenceSummary
│   │   ├── sarif.py          # SARIF フォーマット
│   │   ├── extraction.py     # コード抽出結果
│   │   └── summary.py        # QuerySummary
│   └── ports/                # Protocol（インターフェース定義）
│       ├── project_repository.py   # ProjectRepository Protocol
│       ├── topic_repository.py     # TopicRepository Protocol
│       ├── github_gateway.py       # GitHubGateway + SearchCriteria + GitHubRepositoryDTO
│       ├── codeql_gateway.py       # CodeQLCLIPort, CodeQLDatabaseManagerPort, CodeQLResultAnalyzerPort
│       └── repository_cloner.py    # RepositoryClonerPort
│
├── use_cases/                # === Use Cases 層 ===
│   ├── search_and_store.py         # GitHubGateway + ProjectRepository を注入
│   ├── codeql_database_creation.py # RepositoryClonerPort + CodeQLDatabaseManagerPort を注入
│   ├── codeql_query_execution.py   # CodeQLCLIPort + CodeQLDatabaseManagerPort + CodeQLResultAnalyzerPort を注入
│   ├── benchmark_runner.py         # runner_js_path を keyword-only 引数で外部注入
│   └── visualization.py            # ProjectRepository を注入
│
├── adapters/                 # === Interface Adapters 層 ===
│   ├── cli/                  # 入力アダプター（Typer CLI = composition root）
│   │   ├── __init__.py       # Typer アプリ統合 + main()
│   │   ├── codeql/           # サブパッケージ（create_db, query, summary, extract）
│   │   ├── benchmark.py
│   │   ├── count_lines.py
│   │   ├── github.py
│   │   ├── migrate.py
│   │   ├── search.py
│   │   └── visualize.py
│   ├── repositories/         # DB アダプター（domain/ports/ の Protocol を実装）
│   │   ├── sqlalchemy_project_repo.py
│   │   └── sqlalchemy_topic_repo.py
│   └── gateways/             # 外部連携アダプター
│       ├── github/           # PyGithub 実装（client, search, clone, schema）
│       ├── codeql/           # CodeQL CLI 実装（command, database, analyzer, sarif）
│       ├── visualization/    # matplotlib 実装（boxplot, scatter_plot）
│       └── code_counter/     # JS行数カウンタ（js_counter）
│
├── infrastructure/           # === Frameworks & Drivers 層（最外層）===
│   ├── orm/                  # SQLAlchemy ORM
│   │   ├── base.py           # SQLAlchemy Base
│   │   └── tables.py         # Declarative ORM クラス（ProjectORM, TopicORM）
│   ├── db/                   # DB 接続・セッション管理
│   │   ├── session.py
│   │   └── migrations.py
│   ├── config.py             # pydantic-settings（Settings クラス）
│   └── logging_config.py
│
└── core/                     # 横断的ユーティリティ
    └── cleanup.py

mb-analyzer-legacy/           # [DEPRECATED] 旧 TypeScript analyzer monorepo (pnpm workspace)
├── apps/
│   └── equivalence-runner/   # 旧 equivalence-check コマンドが依存する CLI
│       ├── src/index.ts
│       └── dist/index.js     # ビルド成果物 (esbuild 単一 bundle)
├── features/                 # Package by Feature + 内部に CA 4 層
│   ├── equivalence-check/    # 旧 slow/fast 等価性チェック（後継: mb-analyzer/equivalence-checker）
│   │   └── src/{domain,use-cases,infrastructure}/
│   ├── pattern-mining/       # 旧スケルトン
│   └── rule-codegen/         # 旧スケルトン
├── pnpm-workspace.yaml
└── tsconfig.base.json
# mb-analyzer/ は新 single-package 構成で再構築予定

codeql/                       # CodeQL クエリ設定
tests/                        # テスト（CA 構造をミラー）
├── domain/entities/
├── use_cases/
├── adapters/{cli,repositories,gateways}/
└── infrastructure/{db,test_config,test_logging_config}/
```

### データフロー

1. **検索・保存**: GitHub API検索 → 重複排除 → DB保存 (`SearchAndStoreUseCase`)
2. **解析準備**: リポジトリClone → CodeQL DB作成 (`CodeQLDatabaseCreationUseCase`)
3. **クエリ実行**: クエリ実行 → SARIF解析 → 結果保存 (`CodeQLQueryExecutionUseCase`)
4. **可視化**: DB集計 → グラフ生成 (`VisualizationUseCase`)
5. **ベンチマーク**: Node.js ランナー実行 → 等価性判定 (`BenchmarkRunner`)

---

## 新機能追加ガイド

アーキテクチャの CA レイヤー構造（domain → use_cases → adapters → infrastructure）を遵守すること。

### 1. 新しい CLI コマンドの追加

1. `mb_scanner/adapters/cli/` に新しいPythonファイルを作成する。
2. `Typer` を使用してコマンドと引数を定義する。
3. CLI 内で use_case のインスタンスを組み立て（composition root）、実行する。
4. `mb_scanner/adapters/cli/__init__.py` に新しいコマンドを登録する。

### 2. 新しいドメインモデルの追加

1. `mb_scanner/domain/entities/` に Pydantic BaseModel を定義する。
2. 外部連携が必要な場合は `mb_scanner/domain/ports/` に Protocol を定義する。
3. `mb_scanner/adapters/` で Protocol の具象実装を作成する。

### 3. 新しい Use Case の追加

1. `mb_scanner/use_cases/` に新しいモジュールを作成する。
2. コンストラクタで Protocol を受け取り、具象実装を直接 import しない。
3. CLI の composition root で具象実装を注入する。

### 4. 新しい検索条件の追加

1. `mb_scanner/domain/ports/github_gateway.py` の `SearchCriteria` にフィールドを追加する。
2. `mb_scanner/adapters/gateways/github/search.py` でGitHub APIのクエリ文字列への変換ロジックを実装する。
3. `mb_scanner/adapters/cli/search.py` の引数定義を更新する。

### 5. 新しい可視化の追加

1. `mb_scanner/adapters/gateways/visualization/` に新しいプロット生成モジュールを作成する。
2. `mb_scanner/use_cases/visualization.py` にデータ取得・加工ロジックを追加する。
3. `mb_scanner/adapters/cli/visualize.py` に新しいサブコマンドを追加する。

### 6. データベーススキーマの変更

1. `mb_scanner/infrastructure/orm/tables.py` の該当 ORM クラスを変更する。
2. `mb_scanner/domain/entities/` の対応するドメインモデルも更新する。
3. `mb_scanner/infrastructure/db/migrations.py` にマイグレーション処理を追加する。
4. `mbs migrate` コマンドで既存のデータベースを更新する。

### 7. ベンチマーク機能の拡張

> **DEPRECATED**: 以下は旧 `mb-analyzer-legacy/` 向けの手順。新 equivalence-checker は `mb-analyzer/` に single package 構成で再構築予定のため、新機能はそちらに実装すること。

#### サンドボックス環境のカスタマイズ（旧）

- **安定化処理の追加**: `mb-analyzer-legacy/features/equivalence-check/src/infrastructure/sandbox/stabilizer.ts` に新しい固定化ロジックを追加する。
- **サンドボックスへの統合**: 同 feature の `infrastructure/sandbox/executor.ts` で安定化処理を適用する。

#### 比較ストラテジーの追加（旧）

1. `mb-analyzer-legacy/features/equivalence-check/src/use-cases/strategies/` に新ストラテジーを作成（`canApply()`, `compare()` 実装）
2. `mb-analyzer-legacy/features/equivalence-check/src/use-cases/checker.ts` で戦略リストに追加
3. `mb-analyzer-legacy/features/equivalence-check/src/index.ts` の public export に含める（必要なら）
4. `mb_scanner/domain/entities/benchmark.py` の `comparison_method` Literal に追加
5. テスト追加（`tests/use_cases/test_benchmark_runner.py`）

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
- **ドメインモデル（Pydantic BaseModel）**: `mb_scanner/domain/entities/` に配置する。
- **TypedDict**: 原則として使用するモジュール内に定義する。複数モジュールで再利用する場合のみ `domain/entities/` へ移動する。

### ファイル形式の選択

**JSON を選択すべき場合:**
- データが階層構造を持つ場合（例: SARIF、抽出結果）
- 型情報（文字列/数値/真偽値/null）を区別して保存したい場合
- Pydanticモデルをそのままダンプしたい場合

**CSV を選択すべき場合:**
- Excelやスプレッドシートでの閲覧・分析が主目的の場合
- ネストのない単純なテーブル形式のデータ

### 静的解析ツール

- **Linter/Formatter**: `ruff`（`mise run fix` で実行）
- **Type Checker**: `pyright`（`mise run typecheck` で実行）
- **Architecture**: `import-linter`（`mise run check-arch` で実行）

---

## データベース設計

### 技術スタック

- **RDBMS**: SQLite（サーバーレス、バッチ処理の進捗管理に適しているため）
- **ORM**: SQLAlchemy（宣言的マッピング、`infrastructure/orm/tables.py`）

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

- ORM モデルは `infrastructure/orm/tables.py` に定義（`ProjectORM`, `TopicORM`）。
- ドメインモデル（`domain/entities/project.py` の `Project`, `Topic`）は純粋な Pydantic BaseModel。
- Repository 実装（`adapters/repositories/`）内で ORM ↔ domain の変換を行う。
- リレーション: `ProjectORM.topics` / `TopicORM.projects`、`secondary="project_topics"`、`lazy="selectin"`（N+1回避）
- DB初期化: `mb_scanner.infrastructure.db.session.init_db()` を呼び出す。
- セッション: `SessionLocal()` から Repository 経由でアクセスする。
- **命名規則**: GitHubリポジトリを表す用語は `Project` を使用すること（Repository パターンとの混同を避けるため）。

### 運用上の注意

- `fetched_at` カラムは `datetime.now(UTC)` で自動更新し、再取得の判断基準とする。
