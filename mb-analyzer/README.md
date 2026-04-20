# mb-analyzer

MB-Scanner プロジェクトの TypeScript / Node.js 側コンポーネント。AST 解析、サンドボックス実行、等価性検証、ルール生成など、JavaScript / TypeScript のコード解析タスクを担う。

Python 側 (`mb_scanner/`) からは `dist/cli.js` に対して stdin / stdout の JSON 通信でアクセスされる薄い CLI ラッパーとして利用される。

## 機能

| サブコマンド | 状態 | 役割 |
|---|---|---|
| `check-equivalence` | 実装予定 (Phase 5〜6) | `(setup, slow, fast)` トリプルの意味論的等価性検証 |
| `prune` | 未実装 (将来) | Pruning と構造パターン作成 |
| `equivalence-class-test` | 未実装 (将来) | C1〜C4 条件抽出 + 同値分割テスト |
| `rule-codegen` | 未実装 (将来) | ts-eslint 検出ルール自動生成 |

## セットアップ

```bash
# Node / pnpm バージョンは mise.toml で管理 (node 22 / pnpm 10)
pnpm install
pnpm build          # src/cli/index.ts → dist/cli.js
```

## 開発コマンド

```bash
pnpm build          # esbuild でバンドル
pnpm build:watch    # watch モードでバンドル
pnpm typecheck      # tsc --noEmit
pnpm test           # vitest run
pnpm test:watch     # vitest watch
pnpm lint           # eslint (依存方向検査含む)
pnpm lint:fix       # eslint --fix
```

## ディレクトリ構成

```
src/
├── shared/                    # 共通型 (他機能から import 許可)
├── equivalence-checker/       # 等価性検証器 (Phase 3〜5)
│   ├── sandbox/
│   ├── oracles/
│   ├── checker.ts
│   └── verdict.ts
├── pruning/                   # 将来
├── equivalence-class-test/    # 将来
├── eslint-rule-codegen/       # 将来
└── cli/                       # composition root (全機能統合エントリ)
    ├── index.ts               # サブコマンドルーティング
    └── check-equivalence.ts
tests/                         # vitest
```

### 依存方向ルール

- `shared/` は他機能を import 禁止（型のみの末端層）
- `equivalence-checker/` は `shared/` のみ依存可
- `cli/` は全機能を import 可能（composition root）

`eslint-plugin-import` の `no-restricted-imports` で機械的に強制する。

## セキュリティ上の注意

`equivalence-checker` は Node.js の `vm` モジュールを用いたサンドボックスで JavaScript を評価する。`vm` は Node.js 公式が「信頼できないコードには使うな」と注意喚起しているため、本ツールは **研究者自身が記述したコード断片を評価する用途限定** とする。外部から受け取った任意のコードを評価する目的で使用してはならない。
