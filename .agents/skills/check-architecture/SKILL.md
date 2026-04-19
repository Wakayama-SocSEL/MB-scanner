---
name: check-architecture
description: 実装後にアーキテクチャ・コーディング規約・DB設計の整合性を検証する。Python (mb_scanner/) と TypeScript (mb-analyzer/) で参照ルールが異なるため、変更対象パスから該当ドキュメントを選択して確認する。
allowed-tools: Read, Grep, Glob, Agent
argument-hint: [path]
---

# check-architecture スキル

実装内容が設計ガイドラインに準拠しているかを検証します。本プロジェクトは Python 側 (`mb_scanner/`) と TypeScript 側 (`mb-analyzer/`) で依存方向ルール・静的解析・コーディング規約が異なるため、**変更対象パスに応じて参照すべきドキュメントと検証コマンドを切り替えてください**。

## 参照すべきルールのマッピング

| 変更対象パス | 言語 | 参照ドキュメント | 検証コマンド |
|---|---|---|---|
| `mb_scanner/**`, `tests/**` (ただし `mb-analyzer/tests/` を除く) | Python | `ai-guide/architecture/mb-scanner.md` + `ai-guide/architecture/index.md` | `mise run check-arch`, `mise run typecheck`, `mise run lint`, `mise run test` |
| `mb-analyzer/**` | TypeScript | `ai-guide/architecture/mb-analyzer.md` + `ai-guide/architecture/index.md` | `mise run lint-analyzer`, `mise run typecheck-analyzer`, `mise run test-analyzer` |
| `mb_scanner/domain/entities/equivalence.py` または `mb-analyzer/src/shared/types.ts` が変更された場合 | 両方 (横断契約) | 上記すべて + `index.md` の JSON 契約節 | `mise run check` |
| path 未指定 / 両側に変更あり | 全体 | すべて | `mise run check` |

変更範囲を確認するには `git status` / `git diff --stat` を最初に実行してください。

## Python 側 (`mb_scanner/`) のチェック項目

### アーキテクチャ (Clean Architecture 4 層)

#### 依存方向 (`mise run check-arch` で自動検証)
- [ ] `mise run check-arch` が全契約 PASS するか
- [ ] domain 層が外部フレームワークを import していないか (pydantic は許可。sqlalchemy, typer, github, matplotlib は禁止)
- [ ] use_cases が具象アダプターを直接 import していないか (Protocol / Port を介しているか)

#### ドメイン層の純粋性
- [ ] `domain/entities/` が Pydantic BaseModel のみで構成されているか
- [ ] `domain/ports/` が Protocol のみで構成されているか
- [ ] ビジネスロジックが `use_cases/` に集約されているか

#### Composition Root
- [ ] CLI (`adapters/cli/`) が依存の組み立てを担当しているか
- [ ] Use Case のコンストラクタに Protocol 経由で注入しているか

### コーディング規約
- [ ] `Any` 型を使用していないか
- [ ] 外部入力・設定には Pydantic、内部データには TypedDict を使用しているか
- [ ] ドメインモデルは `mb_scanner/domain/entities/` に配置されているか (dataclass を使っていないか)
- [ ] GitHub リポジトリを表す用語として `Project` を使用しているか (`Repository` は DB パターン用語のため禁止)
- [ ] ファイル形式 (JSON/CSV) の選択が適切か

### 並列バッチ処理 (該当時)
- [ ] `mb_scanner/adapters/cli/_utils.py` の `resolve_workers()` を使って `workers=-1` を解決しているか
- [ ] バッチサイズの auto 決定が `max(10, ceil(total / actual_workers))` に従っているか
- [ ] 進捗表示が stderr の `[progress] N/total ...` 形式のみか (rich / tqdm を導入していないか)

### DB 設計 (DB 関連の変更時のみ)
- [ ] ORM クラスは `infrastructure/orm/tables.py` に定義されているか
- [ ] リレーションに `lazy="selectin"` を設定しているか (N+1 回避)
- [ ] スキーマ変更時に `infrastructure/db/migrations.py` にマイグレーションを追加しているか

### 自動検証コマンド
- `mise run check-arch` — import-linter でレイヤー契約を検証
- `mise run typecheck` — pyright で型チェック
- `mise run lint` — ruff check で Lint
- `mise run test` — pytest

## TypeScript 側 (`mb-analyzer/`) のチェック項目

### 依存方向ゾーン (`mise run lint-analyzer` で自動検証)
- [ ] `mise run lint-analyzer` が PASS するか (`import/no-restricted-paths` のエラーがないか)
- [ ] `shared/` が他機能を import していないか (末端層の維持)
- [ ] `equivalence-checker/` が `pruning/` / `equivalence-class-test/` / `eslint-rule-codegen/` / `cli/` を import していないか
- [ ] 新機能を追加した場合、`eslint.config.js` の `DEPENDENCY_ZONES` にゾーン定義を追加したか
- [ ] `cli/` だけが composition root として全機能を import しているか

### コーディング規約
- [ ] `any` 型を使用していないか (`unknown` + 型ガードで置換)
- [ ] `import type` で型専用 import を使い分けているか (`@typescript-eslint/consistent-type-imports`)
- [ ] `noUncheckedIndexedAccess` を前提に配列/マップアクセスを `T | undefined` として扱っているか
- [ ] ESM 相対パス (`import { foo } from "./bar"` の形、拡張子なし) を使っているか

### サブコマンド CLI 契約
- [ ] 新サブコマンドを追加した場合、`src/cli/index.ts` の `SUBCOMMANDS` に登録したか
- [ ] stdin/stdout 契約 (JSON/JSONL、snake_case、終了コード) を `index.md` の記述と一致させているか
- [ ] サブコマンドのハンドラにビジネスロジックを書いていないか (cli/ は composition root のみ)

### テスト配置
- [ ] `src/` の構造をミラーしたパスに `tests/**/*.test.ts` を配置したか
- [ ] CLI レベル E2E は `tests/cli/`、純粋ロジックは `tests/equivalence-checker/` などに分離したか

### 自動検証コマンド
- `mise run lint-analyzer` — ESLint (依存方向検査込み)
- `mise run typecheck-analyzer` — tsc --noEmit
- `mise run test-analyzer` — vitest
- `mise run build-analyzer` — dist/cli.js のビルド (Python 側 integration test の前に必要)

## 共通契約 (Python ↔ Node JSON 通信)

`mb_scanner/domain/entities/equivalence.py` または `mb-analyzer/src/shared/types.ts` が変更された場合は **両方** を確認:

- [ ] フィールド名が両側とも snake_case で完全一致しているか
- [ ] 列挙値文字列が両側とも完全一致しているか (`"equal"`, `"not_equal"`, `"error"` 等)
- [ ] Python 側 `EquivalenceInput` が `extra="forbid"` のまま維持されているか
- [ ] Python 側 `EquivalenceCheckResult` が `extra="ignore"` のまま維持されているか (TS が将来フィールドを足しても壊れないため)
- [ ] バッチ API 関連の変更では `id` エコーバックと `effective_timeout_ms` の実装が維持されているか
- [ ] `model_dump_json()` に `exclude_defaults=False, exclude_none=False` の明示がある場合、それを維持しているか

## 全体検証

`mise run check` で Python / TypeScript 両側を一括実行する。PR を出す前に必ず通過させること。

```bash
mise run check
```
