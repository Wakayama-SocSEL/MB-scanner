---
name: architecture
description: プロジェクトの全体構造、Clean Architectureのレイヤー設計、データフローを理解する際に使用。また、新機能追加時の実装箇所の特定にも使用します。
allowed-tools: Read, Glob
---

# アーキテクチャガイド

MB-Scannerのアーキテクチャ設計とディレクトリ構造について理解するためのスキルです。

## 参照ファイル
目的に応じて以下の参照ファイルを読み込んでください。

- **全体像・設計思想の把握**: `references/system-design.md`
  - レイヤー構造、依存関係ルール、データフロー、技術選定の理由を確認する場合。
- **実装箇所の特定・拡張**: `references/extension-guide.md`
  - 新しいCLIコマンド、検索条件、可視化機能を追加する際の具体的な手順を確認する場合。
- **ベンチマーク機能の拡張**: `references/benchmark-extension.md`
  - サンドボックス環境のカスタマイズ、比較ストラテジーの追加など、ベンチマーク機能を拡張する場合。

## 重要な設計原則 (抜粋)
- **Clean Architecture**: 依存の方向は `CLI -> Workflows -> Services -> Library/Models` を厳守すること。
- **責務の分離**: ビジネスロジックは `Services`、外部連携は `Library`、複合処理は `Workflows` に配置すること。

---
