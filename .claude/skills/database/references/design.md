# データベース設計詳細

## 技術スタック
- **RDBMS**: SQLite (サーバーレス、バッチ処理の進捗管理に適しているため)
- **ORM**: SQLAlchemy (宣言的マッピングを使用)

## テーブル設計概要

### 1. projects テーブル
GitHubプロジェクト（リポジトリ）の基本情報を保持します。
- **役割**: 重複排除、スター順ソート、データ鮮度管理。
- **主要カラム**:
  - `id`: PK (Integer)
  - `full_name`: UNIQUE / INDEX (String)
  - `stars`: INDEX (Integer)
  - `last_commit_date`: INDEX (DateTime)
  - `fetched_at`: データ取得時刻 (UTC) - 更新判断に使用
  - `js_lines_count`: JavaScript行数

### 2. topics テーブル
トピックのマスタデータです。
- **役割**: トピック名の正規化（LIKE検索の低速化回避と集計容易化のため）。
- **主要カラム**:
  - `id`: PK
  - `name`: UNIQUE / INDEX

### 3. project_topics テーブル
ProjectsとTopicsの多対多中間テーブルです。
- **役割**: トピックベースの検索と集計の効率化。
- **主要カラム**:
  - `project_id`: FK (CASCADE)
  - `topic_id`: FK (CASCADE)
  - 複合主キー: (`project_id`, `topic_id`)

## SQLAlchemy 実装詳細
- **Baseクラス**: すべてのモデルは `Base` を継承し、`Base.metadata.create_all(bind=engine)` で生成されます。
- **リレーション設定**:
  - `Project.topics` / `Topic.projects`
  - `secondary="project_topics"`
  - `back_populates` を使用
  - `lazy="selectin"` (N+1問題回避のため)
- **初期化**:
  - `mb_scanner.db.session.init_db()` を呼び出すことでDBファイルが初期化されます。

## 運用上の注意
- **鮮度管理**: `fetched_at` カラムは `datetime.now(UTC)` で自動更新し、再取得の判断基準とします。
- **セッション**: 操作時は `SessionLocal()` からサービス層（`ProjectService` など）を経由してアクセスしてください。
