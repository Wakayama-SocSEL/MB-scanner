# mb-scanner (Python 側) アーキテクチャ

Python 側コードベース `mb_scanner/` のアーキテクチャ詳細。共通概念と Python ↔ Node 契約は [`index.md`](index.md) を参照。

---

## アーキテクチャ設計

**実用的 Clean Architecture (Pragmatic CA)** を採用しています。依存の方向は常に内側に向かい、内側は外側を知りません。

### レイヤー構造

```
infrastructure（最外層）→ adapters → use_cases → domain（最内層）
  依存は常に内側に向かう。内側は外側を知らない。
```

1. **Domain 層** (`mb_scanner/domain/`)
   - ドメインモデル (Pydantic BaseModel) とポート (Protocol) を定義
   - 許可する外部依存は `pydantic` のみ。`sqlalchemy`, `typer`, `github`, `matplotlib` は禁止
2. **Use Cases 層** (`mb_scanner/use_cases/`)
   - ビジネスロジックを集約。Protocol 経由で依存注入 (DI) を受ける
   - domain にのみ依存し、具象アダプターを直接 import しない
3. **Adapters 層** (`mb_scanner/adapters/`)
   - 入力アダプター (CLI) と出力アダプター (repositories, gateways)
   - CLI は **composition root** として依存の組み立てを担当
   - domain + use_cases に依存。infrastructure へのアクセスも許可 (CLI での DI 組み立て、Repository での ORM 使用)
4. **Infrastructure 層** (`mb_scanner/infrastructure/`)
   - フレームワーク・ドライバー層。ORM 定義、DB 接続、設定、ロギング

### 依存ルールの自動検証

`import-linter` で依存方向を自動チェックしています。

```bash
mise run check-arch   # import-linter でレイヤー契約を検証
```

**契約:**
- **レイヤー契約**: `infrastructure → adapters → use_cases → domain` の順のみ許可
- **ドメイン禁止契約**: domain 層が `sqlalchemy`, `typer`, `github`, `matplotlib` を import していないことを保証
- **例外**: `adapters → infrastructure` は `ignore_imports` で許可 (CLI=composition root, repositories=ORM 実装のため)

---

## ディレクトリ構造

```text
mb_scanner/
├── domain/                   # === Entities 層（最内層）===
│   ├── entities/             # Pydantic BaseModel によるドメインモデル
│   │   ├── project.py        # Project, Topic
│   │   ├── benchmark.py      # EquivalenceResult, EquivalenceSummary
│   │   ├── equivalence.py    # EquivalenceInput, EquivalenceCheckResult, Oracle 列挙
│   │   ├── sarif.py          # SARIF フォーマット
│   │   ├── extraction.py     # コード抽出結果
│   │   └── summary.py        # QuerySummary
│   └── ports/                # Protocol（インターフェース定義）
│       ├── project_repository.py    # ProjectRepository Protocol
│       ├── topic_repository.py      # TopicRepository Protocol
│       ├── github_gateway.py        # GitHubGateway + SearchCriteria + GitHubRepositoryDTO
│       ├── codeql_gateway.py        # CodeQLCLIPort, CodeQLDatabaseManagerPort, CodeQLResultAnalyzerPort
│       ├── equivalence_checker.py   # EquivalenceCheckerPort (check / check_batch)
│       └── repository_cloner.py     # RepositoryClonerPort
│
├── use_cases/                # === Use Cases 層 ===
│   ├── search_and_store.py         # GitHubGateway + ProjectRepository を注入
│   ├── codeql_database_creation.py # RepositoryClonerPort + CodeQLDatabaseManagerPort を注入
│   ├── codeql_query_execution.py   # CodeQLCLIPort + CodeQLDatabaseManagerPort + CodeQLResultAnalyzerPort を注入
│   ├── benchmark_runner.py         # [DEPRECATED] 旧 equivalence-runner 向け
│   ├── equivalence_verification.py # EquivalenceCheckerPort を注入、verify / verify_batch
│   └── visualization.py            # ProjectRepository を注入
│
├── adapters/                 # === Interface Adapters 層 ===
│   ├── cli/                  # 入力アダプター (Typer CLI = composition root)
│   │   ├── __init__.py       # Typer アプリ統合 + main()
│   │   ├── _utils.py         # 共通ヘルパ (resolve_workers 等)
│   │   ├── codeql/           # サブパッケージ (create_db, query, summary, extract)
│   │   ├── benchmark.py      # [DEPRECATED]
│   │   ├── equivalence.py    # check-equivalence / check-equivalence-batch
│   │   ├── count_lines.py
│   │   ├── github.py
│   │   ├── migrate.py
│   │   ├── search.py
│   │   └── visualize.py
│   ├── repositories/         # DB アダプター (domain/ports/ の Protocol を実装)
│   │   ├── sqlalchemy_project_repo.py
│   │   └── sqlalchemy_topic_repo.py
│   └── gateways/             # 外部連携アダプター
│       ├── github/           # PyGithub 実装
│       ├── codeql/           # CodeQL CLI 実装
│       ├── equivalence/      # Node ランナー subprocess 実装 (NodeRunnerEquivalenceGateway)
│       ├── visualization/    # matplotlib 実装
│       └── code_counter/     # JS 行数カウンタ
│
├── infrastructure/           # === Frameworks & Drivers 層（最外層）===
│   ├── orm/                  # SQLAlchemy ORM (tables.py)
│   ├── db/                   # DB 接続・セッション管理 (session.py, migrations.py)
│   ├── config.py             # pydantic-settings (Settings クラス)
│   └── logging_config.py
│
└── core/                     # 横断的ユーティリティ
    └── cleanup.py

tests/                        # テスト (CA 構造をミラー)
├── domain/entities/
├── use_cases/
├── adapters/{cli,repositories,gateways}/
├── fixtures/selakovic/       # 等価性検証の Selakovic 10 パターン fixture
└── infrastructure/{db,test_config,test_logging_config}/
```

---

## データフロー

1. **検索・保存**: GitHub API 検索 → 重複排除 → DB 保存 (`SearchAndStoreUseCase`)
2. **解析準備**: リポジトリ Clone → CodeQL DB 作成 (`CodeQLDatabaseCreationUseCase`)
3. **クエリ実行**: クエリ実行 → SARIF 解析 → 結果保存 (`CodeQLQueryExecutionUseCase`)
4. **可視化**: DB 集計 → グラフ生成 (`VisualizationUseCase`)
5. **等価性検証**: Node ランナー (`mb-analyzer/dist/cli.js`) を subprocess 起動 → 結果を domain モデルに変換 (`EquivalenceVerificationUseCase`)

---

## 新機能追加ガイド

Python 側の CA レイヤー構造 (domain → use_cases → adapters → infrastructure) を遵守すること。

### 1. 新しい CLI コマンドの追加

1. `mb_scanner/adapters/cli/` に新しい Python ファイルを作成する
2. `Typer` を使用してコマンドと引数を定義する
3. CLI 内で use_case のインスタンスを組み立て (composition root)、実行する
4. `mb_scanner/adapters/cli/__init__.py` に新しいコマンドを登録する

### 2. 新しいドメインモデルの追加

1. `mb_scanner/domain/entities/` に Pydantic BaseModel を定義する
2. 外部連携が必要な場合は `mb_scanner/domain/ports/` に Protocol を定義する
3. `mb_scanner/adapters/` で Protocol の具象実装を作成する

### 3. 新しい Use Case の追加

1. `mb_scanner/use_cases/` に新しいモジュールを作成する
2. コンストラクタで Protocol を受け取り、具象実装を直接 import しない
3. CLI の composition root で具象実装を注入する

### 4. 新しい検索条件の追加

1. `mb_scanner/domain/ports/github_gateway.py` の `SearchCriteria` にフィールドを追加する
2. `mb_scanner/adapters/gateways/github/search.py` で GitHub API のクエリ文字列への変換ロジックを実装する
3. `mb_scanner/adapters/cli/search.py` の引数定義を更新する

### 5. 新しい可視化の追加

1. `mb_scanner/adapters/gateways/visualization/` に新しいプロット生成モジュールを作成する
2. `mb_scanner/use_cases/visualization.py` にデータ取得・加工ロジックを追加する
3. `mb_scanner/adapters/cli/visualize.py` に新しいサブコマンドを追加する

### 6. データベーススキーマの変更

1. `mb_scanner/infrastructure/orm/tables.py` の該当 ORM クラスを変更する
2. `mb_scanner/domain/entities/` の対応するドメインモデルも更新する
3. `mb_scanner/infrastructure/db/migrations.py` にマイグレーション処理を追加する
4. `mbs migrate` コマンドで既存のデータベースを更新する

### 7. 並列バッチ処理の追加

- 並列化は **Python 側 `ThreadPoolExecutor`** で実施 (subprocess 起動は I/O バウンドなので GIL 解放される)
- `mb_scanner/adapters/cli/_utils.py` の `resolve_workers(workers)` で `workers=-1 → os.cpu_count() or 1` を統一解決
- バッチサイズの auto 決定は `max(10, ceil(total / actual_workers))` を既存パターンに合わせる
- 進捗は stderr に `[progress] N/total batches done` 形式で出力 (`rich` / `tqdm` は導入しない、nohup 前提)

---

## コーディング規約

### 型定義の原則

`Any` 型の使用は厳禁。

| ユースケース | 推奨する型 | 理由 |
| :--- | :--- | :--- |
| **外部入力の読み込み** | `Pydantic` | 厳密なバリデーションとパース機能が必要なため |
| **設定オブジェクト** | `Pydantic` | デフォルト値の管理や環境変数の読み込みのため |
| **JSON 出力** | `Pydantic` | `model_dump_json()` によるシリアライズとスキーマ生成を活用するため |
| **関数の内部戻り値** | `TypedDict` | ランタイムオーバーヘッドがなく軽量なため |
| **内部データ構造** | `TypedDict` | バリデーション不要で型ヒントのみ必要な場合 |

モデルの配置ルール:
- **ドメインモデル (Pydantic BaseModel)**: `mb_scanner/domain/entities/` に配置する。dataclass は使わない
- **TypedDict**: 原則として使用するモジュール内に定義する。複数モジュールで再利用する場合のみ `domain/entities/` へ移動する

### ファイル形式の選択

**JSON を選択すべき場合:**
- データが階層構造を持つ場合（例: SARIF、抽出結果）
- 型情報（文字列/数値/真偽値/null）を区別して保存したい場合
- Pydantic モデルをそのままダンプしたい場合

**CSV を選択すべき場合:**
- Excel やスプレッドシートでの閲覧・分析が主目的の場合
- ネストのない単純なテーブル形式のデータ

### 命名規則

- **`Project`**: GitHub リポジトリを表す用語（`Repository` は DB パターン用語のため混同回避）
- **`Gateway`**: 外部システム連携アダプター
- **`Port`**: `domain/ports/` の Protocol
- **`Repository`**: DB 永続化アダプター (`adapters/repositories/`)

### 静的解析ツール

- **Linter/Formatter**: `ruff` (`mise run fix` で実行)
- **Type Checker**: `pyright` (`mise run typecheck` で実行)
- **Architecture**: `import-linter` (`mise run check-arch` で実行)

---

## データベース設計

### 技術スタック

- **RDBMS**: SQLite (サーバーレス、バッチ処理の進捗管理に適しているため)
- **ORM**: SQLAlchemy (宣言的マッピング、`infrastructure/orm/tables.py`)

### テーブル設計

**projects テーブル**: GitHub プロジェクト (リポジトリ) の基本情報
- `id`: PK (Integer)
- `full_name`: UNIQUE / INDEX (String)
- `stars`: INDEX (Integer)
- `last_commit_date`: INDEX (DateTime)
- `fetched_at`: データ取得時刻 (UTC) — 更新判断に使用
- `js_lines_count`: JavaScript 行数

**topics テーブル**: トピックのマスタデータ
- `id`: PK
- `name`: UNIQUE / INDEX

**project_topics テーブル**: Projects と Topics の多対多中間テーブル
- `project_id`: FK (CASCADE)
- `topic_id`: FK (CASCADE)
- 複合主キー: (`project_id`, `topic_id`)

### SQLAlchemy 実装詳細

- ORM モデルは `infrastructure/orm/tables.py` に定義 (`ProjectORM`, `TopicORM`)
- ドメインモデル (`domain/entities/project.py` の `Project`, `Topic`) は純粋な Pydantic BaseModel
- Repository 実装 (`adapters/repositories/`) 内で ORM ↔ domain の変換を行う
- リレーション: `ProjectORM.topics` / `TopicORM.projects`、`secondary="project_topics"`、`lazy="selectin"` (N+1 回避)
- DB 初期化: `mb_scanner.infrastructure.db.session.init_db()` を呼び出す
- セッション: `SessionLocal()` から Repository 経由でアクセスする

### 運用上の注意

- `fetched_at` カラムは `datetime.now(UTC)` で自動更新し、再取得の判断基準とする
