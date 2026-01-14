# コーディングガイドライン

## 型定義の原則

本プロジェクトでは、型安全性を重視し、`Any`型の使用を禁止する。

### 必須事項

- **`Any`型は使用禁止**: すべての変数、引数、戻り値に具体的な型を指定すること
- **外部JSONデータ**: Pydanticモデルを使用してバリデーション付きで読み込む
- **内部データ構造**: TypedDictまたはPydanticモデルを使用する

### 型の選択基準

| ユースケース | 推奨する型 | 理由 |
|-------------|-----------|------|
| 外部JSONファイルの読み込み | Pydantic | バリデーション、パース機能が必要 |
| 外部JSONファイルへの出力 | Pydantic | シリアライズ、スキーマ生成が必要 |
| 関数の内部戻り値 | TypedDict | 軽量、バリデーション不要 |
| 設定オブジェクト | Pydantic | バリデーション、デフォルト値が必要 |

### Pydanticモデルの使用例

```python
from pydantic import BaseModel

class QuerySummary(BaseModel):
    query_id: str
    total_projects: int
    results: dict[str, int]

# JSONファイルの読み込み
with open("summary.json", "rb") as f:
    summary = QuerySummary.model_validate_json(f.read())

# JSONファイルへの出力
with open("output.json", "w") as f:
    f.write(summary.model_dump_json(indent=2))
```

### TypedDictの使用例

```python
from typing import TypedDict, Literal

class DatabaseCreationResult(TypedDict):
    status: Literal["created", "skipped", "error"]
    db_path: str | None
    error: str | None

def create_database() -> DatabaseCreationResult:
    return {
        "status": "created",
        "db_path": "/path/to/db",
        "error": None,
    }
```

### モデルの配置

- Pydanticモデルは `mb_scanner/models/` に配置
- TypedDictは使用するモジュール内に定義（再利用する場合は`models/`に移動）

## 外部ファイル形式の選択

### JSON vs CSV

| 観点 | JSON | CSV |
|------|------|-----|
| 構造化データ | ネストした構造を表現可能 | フラットなテーブル形式のみ |
| 型情報 | 文字列/数値/真偽値/null を区別 | すべて文字列として扱われる |
| Pydanticとの相性 | `model_dump_json()` で直接出力可能 | 手動で変換が必要 |
| 他ツール連携 | プログラム間連携に最適 | Excel、スプレッドシートに最適 |
| 人間の可読性 | インデント付きで読みやすい | スプレッドシートで見やすい |
| ファイルサイズ | やや大きい（キー名の重複） | コンパクト |

### 選択基準

**JSONを使うべき場合**
- ネストしたデータ構造がある（SARIF、抽出結果など）
- プログラム間でデータをやり取りする
- Pydanticモデルをそのまま出力したい
- 型情報を保持したい

**CSVを使うべき場合**
- フラットなテーブル形式のデータ
- Excelやスプレッドシートで分析したい
- 大量のレコードを軽量に保存したい

## 型チェック

コード変更後は必ず型チェックを実行すること。

```bash
just typecheck
```
