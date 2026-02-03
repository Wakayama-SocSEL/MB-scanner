---
name: quality-check
description: テストコードの作成、実行、デバッグ、および静的解析（Lint/Type check）を行う際に使用します。
allowed-tools: Bash, Read, Write, Grep, Glob
---

# 品質管理ワークフロー

コードの変更や機能追加を行った際は、必ず以下の手順で品質を担保してください。

## 参照ドキュメント
- [テスト実装ガイドライン](references/guidelines.md)

## 品質チェック手順

実装完了後は、以下の順序でコマンドを実行し、全てパスすることを確認してください。

### 1. 自動テストの実行
機能の動作を保証するため、`pytest` を実行します。
```bash
# 全テスト実行
uv run pytest

# 特定ファイルのテスト（推奨）
uv run pytest tests/path/to/test_file.py
```
### 2. コード整形とLint (Ruff)
コードスタイルを統一するため、修正コマンドを実行します。
```bash
just fix
```
### 3. 型チェック (Pyright)
型安全性を保証するため、型チェックを実行します。
```bash
just typecheck
```

## エラー対応フロー
1. コマンドが失敗した場合、出力されたエラーログを読み取る。
2. エラー原因を特定し、ソースコードまたはテストコードを修正する。
3. 再度コマンドを実行し、パスするまで繰り返す。

---
