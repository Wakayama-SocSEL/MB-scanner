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

### アーキテクチャ
- [ ] レイヤーの依存方向が `CLI -> Workflows -> Services -> Library/Models` になっているか
- [ ] ビジネスロジックが Services 層に適切に配置されているか
- [ ] 外部連携が Library 層に抽象化されているか

### コーディング規約
- [ ] `Any` 型を使用していないか
- [ ] 外部入力・設定には Pydantic、内部データには TypedDict を使用しているか
- [ ] Pydantic モデルは `mb_scanner/models/` に配置されているか
- [ ] ファイル形式（JSON/CSV）の選択が適切か

### DB設計
- [ ] GitHubリポジトリを表す用語として `Project` を使用しているか（`Repository` は禁止）
- [ ] 新しいモデルは `Base` を継承しているか
- [ ] リレーションに `lazy="selectin"` を設定しているか（N+1回避）
- [ ] スキーマ変更時に `mb_scanner/db/migrations.py` にマイグレーションを追加しているか
