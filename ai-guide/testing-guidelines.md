# テストガイドライン

## 必須事項
- すべての新機能に `pytest` ベースの自動テストを追加すること
- DB はインメモリ SQLite（`sqlite:///:memory:`）、フィクスチャは function スコープで隔離
- コード作成後は `pytest` / `just fix` / `just typecheck` を順に実行し、結果を共有

## 最低限のセットアップ
- 共通フィクスチャは `tests/conftest.py` にまとめる
- 代表例
  - `test_db`: エンジン作成 → `Base.metadata.create_all()` → セッション生成 → `finally` でクリーンアップ
  - `topic_service` / `project_service`: `test_db` を受け取りサービスを初期化
- 追加のフィクスチャも Arrange を簡潔に保つ目的でのみ導入する

## テスト構成と命名
- ディレクトリ: `tests/` 以下に対象モジュールへ対応する `test_*.py`
- 関数: `test_` プレフィックス + 条件 + 期待結果（例: `test_save_project_new`）
- Arrange-Act-Assert を意識し、不要なコメントや重複準備を避ける

## カバレッジ指針
- サービス層の public メソッドは必ずテストする
- 各メソッドを 少なくとも 正常系 / 異常・境界系 の 2 ケース以上で確認
- `TopicService` なら「全件新規」「既存混在」「空入力」「存在しない取得」「件数カウント」など典型パターンを網羅

## 重点チェック観点
- 正常系での保存・取得・更新の整合性
- 空・重複・非存在データの扱い
- `update_if_exists` の分岐と関連エンティティ（topics）との整合
- cascade 設定や関連削除の確認

## 実行コマンド
- 基本: `pytest`
- サービス配下のみ: `pytest tests/services/`
- 個別テスト: `pytest tests/services/test_topic_service.py::test_get_or_create_topics_all_new`
- カバレッジ: `pytest --cov=mb_scanner --cov-report=html`

## デバッグ・ベストプラクティス
- 一時的な `print` は `pytest -s` と併用し、終了後に削除
- 必要に応じて `pdb.set_trace()` を使用（コミット前に除去）
- テストは相互依存させず、型ヒントと日本語 docstring で意図を明確にする
