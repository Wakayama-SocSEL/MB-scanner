---
name: check-tests
description: テストの追加・実行・カバレッジ計測・静的解析を行う。Python (mb_scanner/) と TypeScript (mb-analyzer/) で pytest/vitest・モック方針・カバレッジ基準が異なるため、変更対象パスから該当ドキュメントを選択して適用する。
allowed-tools: Read, Grep, Glob, Bash, Agent
argument-hint: [path]
---

# check-tests スキル

テスト網羅性・モック使用・カバレッジ・静的解析を検証する。本プロジェクトは Python 側 (`mb_scanner/`) と TypeScript 側 (`mb-analyzer/`) で使用フレームワーク・モック方針・カバレッジ基準が異なるため、変更対象パスに応じて**参照すべきドキュメントを切り替え、その内容に従って**検証する。

**重要**: チェック項目の master は `ai-guide/quality-check/` 配下のドキュメント。本 SKILL.md は **手順の定義のみ** を担い、チェック項目そのものは重複定義しない（drift 防止）。

---

## 実行手順

### Step 1: 変更範囲の特定

```bash
git status
git diff --stat
```

### Step 2: 対象言語と参照ドキュメントの決定

| 変更対象パス | 言語 | 参照ドキュメント (必ず Read する) |
|---|---|---|
| `mb_scanner/**`, `tests/**` (ただし `mb-analyzer/tests/` を除く) | Python | `ai-guide/quality-check/index.md` + `ai-guide/quality-check/mb-scanner.md` |
| `mb-analyzer/**` | TypeScript | `ai-guide/quality-check/index.md` + `ai-guide/quality-check/mb-analyzer.md` |
| 両側に変更あり / path 未指定 | 全体 | 上記すべて |

### Step 3: 参照ドキュメントを Read して全項目を確認

該当の `ai-guide/quality-check/*.md` を **Read ツールで読み込み**、記載されているチェック項目を **上から順にすべて** 検証する。SKILL.md 側には項目を列挙しないので、必ず ai-guide 側を master として参照すること。

典型的に検証する観点（詳細は ai-guide 側）:
- テスト網羅性（正常系 / 異常系 / 境界系）
- モック方針（何をモックし、何をモックしないか）
- カバレッジ基準（ゾーンごとの目標値）
- 命名・配置・冒頭コメント等のファイル構成規約

### Step 4: 機械検証可能な項目を shell で一括チェック

TypeScript 側に変更がある場合、`scripts/check-ts-test-conventions.sh` を実行して LLM の注意力に依存しない機械検証を走らせる:

```bash
bash .agents/skills/check-tests/scripts/check-ts-test-conventions.sh
```

検査内容:
- `mb-analyzer/tests/**/*.test.ts` に JSDoc 冒頭ブロック (`/**`) が存在するか
- `it.only` / `describe.only` がコミット対象に残っていないか

失敗行があれば修正してから Step 5 へ進む。

### Step 5: 検証コマンド実行

**Python 単体変更**:
```bash
mise run lint
mise run typecheck
mise run test
mise run test-cov    # 必要な場合のみ
```

**TypeScript 単体変更**:
```bash
mise run lint-analyzer
mise run typecheck-analyzer
mise run test-analyzer
mise run test-analyzer-cov    # 必要な場合のみ
```

**両側変更 / PR 前最終確認**:
```bash
mise run check    # Lint + 型チェック + テスト + アーキ検証を一括実行
```

### Step 6: 結果の集約・修正

- 未到達分岐・失敗テストがあれば追加・修正
- カバレッジ未達箇所を ai-guide の基準と照合
- `mise run check` が PASS しない状態で PR は出さない

---

## チェック項目が SKILL.md にない理由

チェック項目 (何を検証するか) は `ai-guide/quality-check/` 側で一元管理する。SKILL.md に複製すると、ai-guide を更新したときに SKILL.md 側が置き去りになり、漏れが発生する (drift)。本 skill は「手順 + マッピング + 検証コマンド」のみを持つ責務分離にしている。

ルールを追加・変更したいときは `ai-guide/quality-check/` を編集すればよく、SKILL.md の更新は不要。
