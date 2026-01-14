# 型生成コマンド

JSONファイルからPydantic v2モデルを自動生成し、`mb_scanner/models/`に配置するコマンドです。

## 引数

$ARGUMENTS: 入力ファイルパス（.json または .sarif）

## 実行手順

### 1. 入力ファイルの確認

指定されたファイルの存在と形式を確認してください：
- `.json`ファイル: そのまま処理
- `.sarif`ファイル: 中身はJSON形式なので、そのまま`--input-file-type json`で処理可能

### 2. datamodel-codegenで初期モデル生成

以下のコマンドで一時ファイルにモデルを生成します：

```bash
datamodel-codegen \
  --input "$ARGUMENTS" \
  --input-file-type json \
  --output-model-type pydantic_v2.BaseModel \
  --output /tmp/generated_model.py \
  --use-annotated \
  --field-constraints \
  --target-python-version 3.12
```

### 3. 生成されたモデルのレビュー

生成されたファイル `/tmp/generated_model.py` を読み込み、以下の観点で整理してください：

#### 命名の最適化
- クラス名がわかりやすいか確認（例: `Model` → `SarifReport`）
- フィールド名がPython命名規則に従っているか確認
- 重複した名前（例: `Properties1`, `Region1`）を意味のある名前に変更

#### 型の整理
- `Any`が残っている箇所を具体的な型に置き換え可能か検討
- Optional型の適切な使用
- Enumの導入が適切な箇所（例: severity → `Literal["warning", "error", "note"]`）
- **動的キーを持つ辞書の処理**: リポジトリ名など動的キーの場合は `dict[str, int]` に変更

#### 構造の整理
- ネストが深すぎる場合は別クラスに分離
- 共通の構造はベースクラスに抽出
- 不要なフィールドの削除

#### 特殊ケースの対応
- **サマリーJSON**: `results`フィールドが動的なリポジトリ名をキーとする場合、生成されたクラスを `dict[str, int]` に置き換え

### 4. 出力ファイル名の決定

入力ファイルの種類に応じて出力先を決定：

| 入力ファイルの種類 | 出力ファイル |
|---|---|
| SARIFファイル (*.sarif) | `mb_scanner/models/sarif.py` |
| サマリーJSON (summary*.json) | `mb_scanner/models/summary.py` |
| 抽出コードJSON (*_code.json, tmp.json) | `mb_scanner/models/extraction.py` |
| その他 | ユーザーに確認 |

### 5. モデルファイルの作成

整理したモデルを出力先に書き込みます。

ファイルの先頭には以下のdocstringを追加：

```python
"""[モデルの説明]

このモジュールは datamodel-code-generator によって自動生成され、
AIによって整理されました。

元ファイル: [入力ファイルパス]
生成日時: [現在日時]
"""
```

### 6. `__init__.py`の更新

`mb_scanner/models/__init__.py` に新しいモデルのインポートを追加します。

### 7. 品質チェック

```bash
# 型チェック
just typecheck

# フォーマット
just fix
```

## 使用例

```
/generate-types outputs/queries/id_10/facebook-react.sarif
/generate-types outputs/queries/detect_strict/summary/id_10_limit_1.json
/generate-types outputs/extracted_code/tmp.json
```

## 注意事項

- 生成されたモデルは必ずAIがレビューし、プロジェクトのコーディング規約に合わせて調整すること
- 既存のモデルファイルがある場合は上書きする前にユーザーに確認すること
- SARIFファイルは標準フォーマットなので、公式スキーマ（https://json.schemastore.org/sarif-2.1.0.json）も参考にすること
