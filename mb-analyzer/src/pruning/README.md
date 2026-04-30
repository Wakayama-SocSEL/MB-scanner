# pruning

構造パターン導出エンジン。`(slow, fast, setup)` トリプルから **ワイルドカード付きの最小構造パターン** を出力する。`engine.prune()` が公開エントリポイント。

## ファイル index

```
src/pruning/
├── engine.ts            ← 公開 prune + tryPruneCandidates (mutate + revert / savepoint パターン)
├── candidates.ts        ← enumerateCandidates (3 段フィルタ + size 降順)
├── index.ts             ← 公開 re-export
├── rules/               ← pruning が扱う対象と戦略の宣言データ集
│   ├── index.ts            ← barrel
│   ├── whitelist.ts        ← WHITELIST_CATEGORIES (型 → カテゴリ) + PARSER_PLUGINS
│   ├── blacklist.ts        ← BLACKLIST_CATEGORIES (`@babel/types` 文法メタから自動導出)
│   └── replacement.ts      ← REPLACEMENTS (カテゴリ → placeholderKind + buildNode)
└── ast/                 ← Babel AST 汎用 toolbox (pruning 知識ゼロ)
    ├── parser.ts           ← parse / generate / tryGenerateNode (Babel ラッパ)
    ├── walk.ts             ← walkNodes / isNode (VISITOR_KEYS ベースの DFS 走査)
    ├── inspect.ts          ← countNodes / snippetOfNode (read-only AST 検査)
    └── fast-subtree-set.ts ← FastSubtreeSet (top-down subtree hash で fast 所属判定)
```

3 層の役割分担:

| 層 | 中身 | pruning 知識 | 入れ替え可能性 |
|---|---|---|---|
| ルート (engine, candidates) | アルゴリズム本体 | あり | このプロジェクト固有 |
| `rules/` | 宣言データのみ (whitelist / blacklist / replacement) | あり | データ差し替え可能 |
| `ast/` | parser / walk / inspect / subtrees (Babel AST toolbox) | なし | 別プロジェクトに切り出し可能 |

## 依存方向

```
engine.ts
 ├─ candidates.ts ──┬─ rules/whitelist.ts
 │                  ├─ rules/blacklist.ts ── rules/whitelist.ts
 │                  ├─ ast/subtrees.ts ── ast/walk.ts
 │                  └─ ast/walk.ts
 ├─ rules/replacement.ts ── rules/whitelist.ts
 ├─ ast/parser.ts ── rules/whitelist.ts (PARSER_PLUGINS)
 ├─ ast/inspect.ts ── ast/walk.ts
 └─ ../equivalence-checker (上層モジュール)
```

葉ノードは `rules/whitelist.ts` / `ast/parser.ts` / `ast/walk.ts` (Babel のみに依存)。

## 関連 ADR

- [ADR-0001](../../../ai-guide/adr/0001-pruning-ast-traversal.md): AST 走査に `VISITOR_KEYS` 再帰を採用 (`ast/walk.ts`)
- [ADR-0002](../../../ai-guide/adr/0002-babel-topdown-subtree-hash.md): AST 差分判定に Babel + top-down subtree hash を自作 (`ast/subtrees.ts`)
- [ADR-0003](../../../ai-guide/adr/0003-bottom-up-mapping-deferred.md): bottom-up mapping を第 2 段階以降に遅延
- [ADR-0004](../../../ai-guide/adr/0004-pruning-setup-single.md): `PruningInput.setup` を単数 string にする
- [ADR-0005](../../../ai-guide/adr/0005-grammar-derived-blacklist.md): 候補位置 blacklist を文法メタから自動導出 (`rules/blacklist.ts`)
- [ADR-0006](../../../ai-guide/adr/0006-grammar-derived-whitelist.md): 候補型 whitelist を alias 由来で自動導出 (`rules/whitelist.ts`)
- [ADR-0007](../../../ai-guide/adr/0007-in-source-testing-internal-helpers.md): 内部ヘルパとモジュール内共有ヘルパは in-source testing、公開 API は `tests/` ツリーで分離する
- [ADR-0008](../../../ai-guide/adr/0008-mutate-revert-replacement.md): 候補置換を mutate + revert (savepoint パターン) で実装し `cloneAst` を廃止
