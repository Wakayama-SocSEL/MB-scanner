---
name: database
description: データベースのスキーマ変更、SQLAlchemyモデルの定義、マイグレーション、クエリ作成を行う際に使用します。
allowed-tools: Read, Grep
---

# データベースエンジニアリング

SQLite + SQLAlchemyを使用したデータベースの設計・変更ガイドラインです。
DB関連のタスクを行う際は、以下の参照ドキュメントを確認し、整合性を維持してください。

## 参照ドキュメント
- [詳細設計書](references/design.md)

## 重要な命名規則
- **ドメイン名**: GitHubリポジトリを表す用語として、`Repository` ではなく **`Project`** を使用すること（Repositoryパターンの実装と混同しないため）。

## DB変更ワークフロー
スキーマを変更する場合は、以下の手順に従ってください：
1. `mb_scanner/models/` 内のモデル定義を変更する。
2. `mb_scanner/db/migrations.py` にマイグレーション処理を追加する（Alembicは未導入のため）。
3. 以下のコマンドでマイグレーションを実行し、動作確認を行う。
   ```bash
   uv run mbs migrate
   ```

## クエリ作成の注意点
- 多対多のリレーション（Project-Topic）は lazy="selectin" が設定されているため、N+1問題を意識せずアクセス可能ですが、大量データ取得時は注意してください。

---
