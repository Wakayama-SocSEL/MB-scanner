# pruning

構造パターン導出エンジン。`(slow, fast, setup)` トリプルから **ワイルドカード付きの最小構造パターン** を出力する。`engine.prune()` が公開エントリポイント。

## ファイル index

| file | 役割 | 主な依存 |
|---|---|---|
| `engine.ts` | 公開 `prune` + 1 パス試行 `tryPruneCandidates`。Hydra 反復ループ本体 | `ast/candidates`, `ast/replace`, `ast/inspect`, `categories`, `equivalence-checker` |
| `categories.ts` | `NodeCategory → mode + placeholderKind` dispatch (HANDLERS) | `constants`, `shared/types`, `ast/replace` |
| `constants.ts` | `NODE_CATEGORY` (whitelist 兼カテゴリ分類)、`PARSER_PLUGINS` | `@babel/types` |
| `index.ts` | 公開 re-export | (none) |
| `ast/parser.ts` | `parse` / `generate` / `tryGenerateNode` (Babel ラッパ) | `@babel/parser`, `@babel/generator` |
| `ast/candidates.ts` | `enumerateCandidates` (3 段フィルタ + size 降順) | `constants`, `ast/diff`, `ast/grammar-blacklist` |
| `ast/replace.ts` | `replaceNode` (1 箇所書き換え + round-trip 検証) | `ast/parser` |
| `ast/diff.ts` | `SubtreeDiff` (top-down subtree hash で fast 共通ノード判定) | `@babel/types` |
| `ast/grammar-blacklist.ts` | `getGrammarBlacklist` (`@babel/types` 文法メタから自動導出) | `constants` |
| `ast/inspect.ts` | `countNodes` / `snippetOfNode` (read-only AST 検査) | `ast/parser` |

## 依存方向

```
engine.ts
 ├─ categories.ts ─── constants.ts
 ├─ ast/candidates.ts ─┬─ ast/grammar-blacklist.ts ─ constants.ts
 │                     ├─ ast/diff.ts
 │                     └─ constants.ts
 ├─ ast/replace.ts ─── ast/parser.ts
 ├─ ast/inspect.ts ─── ast/parser.ts
 └─ ../equivalence-checker (上層モジュール)
```

葉ノードは `constants.ts` / `ast/parser.ts` / `ast/diff.ts` (Babel のみに依存)。

## 関連 ADR

- [ADR-0001](../../../ai-guide/adr/0001-pruning-ast-traversal.md): AST 走査に `VISITOR_KEYS` 再帰を採用
- [ADR-0002](../../../ai-guide/adr/0002-babel-topdown-subtree-hash.md): AST 差分判定に Babel + top-down subtree hash 自作 (`ast/diff.ts`)
- [ADR-0003](../../../ai-guide/adr/0003-bottom-up-mapping-deferred.md): bottom-up mapping を第 2 段階以降に遅延
- [ADR-0004](../../../ai-guide/adr/0004-pruning-setup-single.md): `PruningInput.setup` を単数 string にする
- [ADR-0005](../../../ai-guide/adr/0005-grammar-derived-blacklist.md): 候補位置 blacklist を文法メタから自動導出 (`ast/grammar-blacklist.ts`)
- [ADR-0006](../../../ai-guide/adr/0006-grammar-derived-whitelist.md): 候補型 whitelist を alias 由来で自動導出 (`constants.ts`)
- [ADR-0007](../../../ai-guide/adr/0007-in-source-testing-internal-helpers.md): 内部ヘルパは in-source testing (`ast/candidates.ts`、`ast/grammar-blacklist.ts`、`ast/diff.ts` で適用中)
