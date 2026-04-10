---
name: check-tests
description: テストコードの作成・実行・デバッグ、および静的解析（Lint/Type check）を行う際に使用します。テスト網羅性・モック使用・品質基準が守られているか確認します。
allowed-tools: Read, Grep, Glob, Agent
argument-hint: [path]
---

# check-tests スキル

テスト品質の検証と静的解析を行います。

## 参照ドキュメント

`.claude/ai-guide/quality-check.md` を読み込んでガイドラインに従ってください。

## チェック項目

### テスト実装
- [ ] 新機能に対して `pytest` ベースのテストが追加されているか
- [ ] DBテストでインメモリSQLite (`sqlite:///:memory:`) を使用しているか
- [ ] フィクスチャは `function` スコープで隔離されているか

### カバレッジ
- [ ] `mb_scanner/services/` の public メソッドが 100% テストされているか
- [ ] 正常系と異常・境界系の両方がカバーされているか

### モック
- [ ] Library Layer（`mb_scanner/lib/`）がモック化されているか
- [ ] 外部 API 通信・外部コマンド実行がモック化されているか
- [ ] DB（SQLAlchemy セッション）はモックしていないか

## 品質チェックコマンド

```bash
# テスト実行
uv run pytest                                        # 全テスト
uv run pytest tests/path/to/test.py                 # 特定ファイル
uv run pytest tests/path/to/test.py::func_name      # 特定テスト関数

# フォーマット・Lint
just fix

# 型チェック
just typecheck
```

## 作業完了時のチェック順序

1. `just fix`
2. `just typecheck`
3. `uv run pytest`
