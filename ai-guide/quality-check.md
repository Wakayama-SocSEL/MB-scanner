# テスト実装ガイドライン

## 基本方針

- **必須事項**: 新機能の実装には必ず `pytest` ベースのテストを追加すること。
- **DBテスト**: テストの独立性と速度を保つため、インメモリSQLite (`sqlite:///:memory:`) を使用する。
- **スコープ**: フィクスチャは原則として `function` スコープで隔離し、テスト間の依存を排除する。

## ディレクトリ構成と命名

- **配置**: `tests/` 以下に CA 構造をミラーした形で配置する。
  ```
  tests/
  ├── domain/entities/          # ドメインモデルのテスト
  ├── use_cases/                # Use Case のテスト
  ├── adapters/
  │   ├── cli/                  # CLI コマンドのテスト
  │   ├── repositories/         # Repository 実装のテスト
  │   └── gateways/             # Gateway 実装のテスト
  │       ├── github/
  │       ├── codeql/
  │       ├── visualization/
  │       └── code_counter/
  └── infrastructure/           # DB接続・設定のテスト
  ```
- **関数名**: `test_` プレフィックス + 条件 + 期待結果（例: `test_save_project_new`）。

## フィクスチャ (conftest.py)

共通のセットアップ処理は `tests/conftest.py` に集約されています。
- `test_db`: エンジン作成・テーブル作成・セッション生成・クリーンアップを一括管理する。
- **原則**: Arrangeフェーズを簡潔に保つため、共通化できるものはフィクスチャ化すること。

## カバレッジ基準

- **Use Cases 層**: `mb_scanner/use_cases/` 配下の public メソッドは**100%テスト**すること。
- **Repository 層**: `mb_scanner/adapters/repositories/` の CRUD 操作は**100%テスト**すること。
- **ケース網羅**: 各メソッドに対し、少なくとも以下の2パターンを確認すること。
  - **正常系**: 期待通りに保存・取得・更新ができるか。
  - **異常・境界系**: 空入力、重複データ、存在しないIDへのアクセス、Cascade削除の挙動など。
- **エッジケース**: 文字列処理や配列操作ではパターンの違いを網羅すること。
  - 例: JSONフォーマット処理 → プリミティブ配列、オブジェクト配列、ネスト配列の各ケース
  - 例: 正規表現マッチ → マッチする/しない境界条件を複数テスト

## モック化の指針

### モックすべき対象

- **Gateway 層**: `mb_scanner/adapters/gateways/` 配下のクラス（GitHub, CodeQL, visualization）
- **外部 API 通信**: 実際に HTTP リクエストを送信してはならない
- **外部コマンド実行**: `subprocess` による CodeQL や git コマンドの実行

### モックしてはいけない対象

- **Database**: `sqlite:///:memory:` を使用し、SQLAlchemy のセッション自体はモックしないこと（クエリの整合性を確認するため）
- **Pydantic Models**: ドメインエンティティは実体を使用する

### 実装方法

- **ツール**: `unittest.mock` または `pytest-mock`（`mocker` フィクスチャ）を使用する。
- **DI**: Use Case のテストでは、コンストラクタで受け取る Protocol をモックに置き換える。

```python
# 良い例: Protocol をモックして Use Case をテスト
def test_search_and_store(mocker):
    mock_gateway = mocker.Mock(spec=GitHubGateway)
    mock_gateway.search_repositories.return_value = [...]
    mock_repo = mocker.Mock(spec=ProjectRepository)
    use_case = SearchAndStoreUseCase(gateway=mock_gateway, repository=mock_repo)
    use_case.execute(...)
    mock_gateway.search_repositories.assert_called_once()
```

## デバッグのヒント

- 一時的なデバッグには `print()` と `pytest -s` を併用しても良いが、コミット前に必ず削除すること。
- 複雑なロジックの確認には `pdb.set_trace()` の使用を許可するが、これもコミット前に除去すること。
