# mb-analyzer-legacy

**DEPRECATED**: このディレクトリは旧 `mb-analyzer/` を退避したもの。

## 位置付け

- 旧 `mbs benchmark equivalence-check` コマンド（JSONL 一括チェック）が依存するビルド成果物（`apps/equivalence-runner/dist/index.js`）を生成するために残している。
- 新 equivalence-checker（1トリプル単位の判定）は新 `mb-analyzer/` に single package 構成で再構築される。
- 新機能追加はここではなく新 `mb-analyzer/` に対して行うこと。

## 構成

```
mb-analyzer-legacy/
├── apps/
│   └── equivalence-runner/   # 旧 Python-CLI 連携用ランナー
├── features/
│   ├── equivalence-check/    # 旧 slow/fast 等価性チェックの戦略群
│   ├── pattern-mining/       # 空スケルトン（未実装）
│   └── rule-codegen/         # 空スケルトン（未実装）
├── pnpm-workspace.yaml
└── tsconfig.base.json
```

## ビルド

```bash
pnpm --prefix mb-analyzer-legacy install
pnpm --prefix mb-analyzer-legacy run build
```

あるいは mise タスク（いずれも `[DEPRECATED]` 接頭辞）:

```bash
mise run build-analyzer-ts
mise run test-analyzer-ts
mise run typecheck-ts
```

## 廃止予定

新 equivalence-checker（`mbs check-equivalence`）が Selakovic 10 パターン全件で安定稼働し、旧コマンドの呼び出し元が全て移行し次第、このディレクトリは削除される。
