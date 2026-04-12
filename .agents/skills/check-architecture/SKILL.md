---
name: check-architecture
description: 実装後にアーキテクチャ・コーディング規約・DB設計の整合性を検証する。レイヤー違反（CLIがServicesを直接呼ぶなど）、Any型の使用、命名規則の違反がないか確認する際に使用します。
allowed-tools: Read, Grep, Glob, Agent
argument-hint: [path]
---

# check-architecture スキル

実装内容が設計ガイドラインに準拠しているかを検証します。

## 参照ドキュメント

`.claude/ai-guide/architecture.md` を読み込んで以下を確認してください。

## チェック項目

### アーキテクチャ（Clean Architecture 4層構造）

#### 依存方向（`mise run check-arch` で自動検証）
- [ ] `mise run check-arch` が全契約 PASS するか
- [ ] domain 層が外部フレームワークを import していないか（pydantic は許可。sqlalchemy, typer, github, matplotlib は禁止）
- [ ] use_cases が具象アダプターを直接 import していないか（Protocol / Port を介しているか）

#### ドメイン層の純粋性
- [ ] `domain/entities/` が Pydantic BaseModel のみで構成されているか
- [ ] `domain/ports/` が Protocol のみで構成されているか
- [ ] ビジネスロジックが `use_cases/` に集約されているか

#### Composition Root
- [ ] CLI（`adapters/cli/`）が依存の組み立てを担当しているか
- [ ] Use Case のコンストラクタに Protocol 経由で注入しているか

### コーディング規約
- [ ] `Any` 型を使用していないか
- [ ] 外部入力・設定には Pydantic、内部データには TypedDict を使用しているか
- [ ] ドメインモデルは `mb_scanner/domain/entities/` に配置されているか
- [ ] GitHubリポジトリを表す用語として `Project` を使用しているか（`Repository` は禁止）
- [ ] ファイル形式（JSON/CSV）の選択が適切か

### DB設計
- [ ] ORM クラスは `infrastructure/orm/tables.py` に定義されているか
- [ ] リレーションに `lazy="selectin"` を設定しているか（N+1回避）
- [ ] スキーマ変更時に `infrastructure/db/migrations.py` にマイグレーションを追加しているか

### 自動検証コマンド
- `mise run check-arch` — import-linter でレイヤー契約を検証
- `mise run typecheck` — pyright --strict で型チェック
- `mise run lint` — ruff check で Lint
- `mise run check` — 上記全てを一括実行
