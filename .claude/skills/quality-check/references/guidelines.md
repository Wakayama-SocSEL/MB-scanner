# テスト実装ガイドライン

## 基本方針
- **必須事項**: 新機能の実装には必ず `pytest` ベースのテストを追加すること。
- **DBテスト**: テストの独立性と速度を保つため、インメモリSQLite (`sqlite:///:memory:`) を使用する。
- **スコープ**: フィクスチャは原則として `function` スコープで隔離し、テスト間の依存を排除する。

## 実装の詳細ルール

### 1. ディレクトリ構成と命名
- **配置**: `tests/` ディレクトリ以下に、実装モジュールと対応する形で配置する（例: `tests/services/test_project_service.py`）。
- **関数名**: `test_` プレフィックス + 条件 + 期待結果（例: `test_save_project_new`）。

### 2. フィクスチャ (conftest.py)
共通のセットアップ処理は `tests/conftest.py` に集約されています。
- `test_db`: エンジンの作成、テーブル作成、セッション生成、クリーンアップを一括管理します。
- `service`: `test_db` セッションを受け取り、サービスインスタンスを初期化します。
- **原則**: Arrange（準備）フェーズを簡潔に保つため、共通化できるものはフィクスチャ化してください。

### 3. カバレッジ基準
- **サービス層**: `mb_scanner/services/` 配下の public メソッドは**100%テスト**すること。
- **ケース網羅**: 各メソッドに対し、少なくとも以下の2パターンを確認すること。
  - **正常系**: 期待通りに保存・取得・更新ができるか。
  - **異常・境界系**: 空入力、重複データ、存在しないIDへのアクセス、Cascade削除の挙動など。

## デバッグのヒント
- 一時的なデバッグには `print()` と `pytest -s` を併用しても良いが、コミット前に必ず削除すること。
- 複雑なロジックの確認には `pdb.set_trace()` の使用を許可するが、これもコミット前に除去すること

## モック化の指針 (Mocking Strategy)

外部システムや重い処理に依存するコンポーネントは、適切にモック化してテストの独立性と速度を維持してください。

### 1. モックすべき対象 (Must Mock)
以下のレイヤーや操作を含むテストでは、原則としてモックを使用してください。
- **Library Layer**: `mb_scanner/lib/` 配下のクラス（GitHubClient, CodeQLCLI など）。
- **外部 API 通信**: 実際に HTTP リクエストを送信してはならない。
- **外部コマンド実行**: `subprocess` による CodeQL や git コマンドの実行。

### 2. モックしてはいけない対象 (Don't Mock)
- **Database**: 前述の通り `sqlite:///:memory:` を使用し、**SQLAlchemy のセッション自体はモックしない**こと（クエリの整合性を確認するため）。
- **Pydantic Models / Data Classes**: 単なるデータ構造は実体を使用する。

### 3. 実装方法
- **ツール**: `unittest.mock` (標準ライブラリ) または `pytest-mock` (`mocker` フィクスチャ) を使用する。
- **DI (依存性注入)**: Service 層のテストでは、コンストラクタや引数で渡される Library クラスを `MagicMock` に置き換えてテストする。

### 実装例
```python
# 良い例: GitHubClient をモックして Service をテスト
def test_search_projects(mocker):
    # Arrange
    mock_client = mocker.Mock(spec=GitHubClient)
    mock_client.search_repositories.return_value = [...]  # ダミーデータ
    service = ProjectSearchService(client=mock_client)

    # Act
    service.execute(...)

    # Assert
    mock_client.search_repositories.assert_called_once()
```
