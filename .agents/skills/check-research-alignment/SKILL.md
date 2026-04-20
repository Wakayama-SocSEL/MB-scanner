---
name: check-research-alignment
description: 研究計画 (current.md) と実装の整合性を能動的にチェックする。「この実装は研究方針と合ってる？」「いま書いているコードは current.md のどこに対応する？」「次に何を実装すべき？」「この設計判断の根拠は？」「方針からずれていないか？」「code-map に追加すべき実装は？」など、実装と研究計画の照合に関わる文脈で必ずこのスキルを使う。MB-scanner のソースコードを編集している時、ai-research-workspace で実装計画を立てている時、設計判断・優先度・整合性に関する質問が来たら、明示的に呼ばれなくても自動でこのスキルを発火させること
---

# check-research-alignment スキル

研究計画 (`current.md`) と実装の整合性を能動的にチェックするスキル。
ai-research-workspace と MB-scanner (ソースコード側) の両方から呼ばれる。

`query-wiki` が「事実ベース (論文・概念の定義)」を扱うのに対し、本スキルは「**主張ベース** (本研究の方針・段階・設計判断)」と実装の整合性チェックに特化する。

## 起動時の workspace 判定 (必ず最初に実行)

`pwd` で現在のディレクトリを確認し、以下のロジックで参照ファイルを決める。**両モードでファイル名が異なる**理由は、ソースコード側にコピーされる時にリネームされる規約 (`current.md` → `current-research.md`) のため。

| 起動モード | 判定条件 | 主参照 | 補参照 |
|---|---|---|---|
| **ai-research モード** | `my-research/current.md` が存在 | `my-research/current.md` | `my-research/code-map.md` |
| **source-code モード** | `ai-guide/current-research.md` が存在 | `ai-guide/current-research.md` | (なし) |
| **対象外** | 上記いずれもなし | — | — |

判定がつかない場合は「研究計画ファイルが見つからない」と明示して、対象外として処理を中断する。

source-code モードで `ai-guide/current-research.md` が古い疑いがあるなら、ユーザーに「ai-research-workspace 側で `bash .agents/hooks/sync-to-source.sh` を実行して同期してください」と提案する。

## 質問パターンと対応手順

ユーザーの問いを以下に分類して処理する。複数該当なら順に答える。

### A. 整合性チェック (例: 「この実装は研究方針と合ってる？」「方針からずれてない？」)

1. 対象コード (ファイル / 関数 / 編集中の差分) を Read
2. `current.md` から該当する段階・節を Grep で特定 (キーワード一致 or §章番号)
3. コードが満たすべき要件 (current.md が要求すること) と実際の実装を比較
4. **整合・ずれ・抜け** を構造化して報告 (フォーマットは下記)

### B. マッピング (例: 「これは current.md のどこに対応？」「§4 C-2 の実装はどこ？」)

1. 対象コード or §章番号を確認
2. ai-research モードなら `code-map.md` を Read して既存マッピングを確認
3. `current.md` の該当 §章を file:line で引用
4. code-map に未登録なら「追加すべき」と提案 (ai-research モードのみ)

### C. 進捗・優先度 (例: 「次に何を実装すべき？」「いまどこ？」)

1. `current.md` の「3 段階のアプローチ」「スケジュール」「貢献」セクションを Read
2. ai-research モードなら `code-map.md` で実装済み / 未実装を確認
3. 締切 (`current.md` frontmatter の `goal` / `status`) と未実装項目を突き合わせて優先度を提案

### D. 設計判断の根拠 (例: 「なぜ実行ベース pruning？」「Graded Soundness を入れる理由は？」)

1. `current.md` から該当判断を Grep
2. 引用付きで返す。研究の主張と実装の関係を明示

### E. code-map 追加提案 (ai-research モード専用)

1. MB-scanner の実装ファイル一覧を Glob (`~/dev/research/MB-scanner/main/mb_scanner/**/*.py` 等)
2. `code-map.md` に記載のないファイルを検出
3. `current.md` の §章 (主に §4 C-1〜C-5) と照合して追加すべきエントリを提案

## 出力フォーマット

### A の報告 (整合性チェック)

```markdown
## 対象
- 実装: <ファイルパス or 関数>
- 研究方針との対応: current.md §<章番号> <章タイトル>

## 整合
- <要件>: <コードがこう満たしている> (`<file>:<line>`)

## ずれ・抜け
- <要件>: <コードでこうなっているが、current.md ではこう要求> (`<file>:<line>`)

## 設計判断の根拠
- `current.md:<line>` より引用: "<原文>"

## 不確実性
- <情報不足で判断できない箇所があれば明示>
```

### B の出力 (マッピング)

```markdown
## マッピング
- 実装: `<file>:<line>` <説明>
- 対応: current.md §<章> <章タイトル> (`current.md:<line>`)
- code-map 登録状況: あり / なし (なしなら追加提案)
```

### C の出力 (進捗)

```markdown
## 現在地
- 締切: <goal> (current.md frontmatter)
- 完了: <code-map から抽出 or 未確認>
- 未着手: <code-map から抽出>

## 次の優先順位
1. <項目> — 理由: <依存関係 / スケジュール / 貢献度>
2. ...
```

## 引用と根拠のポリシー

- **`current.md` / `code-map.md` に書いてあることだけを根拠として述べる**。書かれていない判断は「current.md に記載なし」と明示
- 推測は「これは推測ですが」と前置き
- file:line 引用 (`my-research/current.md:42` or `ai-guide/current-research.md:42`) を必ず付ける。ユーザーがクリックでジャンプできる形式
- 整合性が判断できない (情報不足) 場合は「不明」と返し、何が分かれば判断できるかを示す

## 注意事項

- `current.md` 全体を毎回 Read しない。必要な節だけ Grep で絞る (現状 400+ 行)
- 重大な変更提案 (current.md の修正案など) は必ずユーザーに確認
- `code-map.md` は ai-research モードでのみ参照 (source-code モードには存在しない)
- このスキルは**読み取りと提案**のみ。`current.md` / `code-map.md` の編集はユーザー (or 別タスク) に委ねる

## 関連スキル

- `query-wiki`: 事実照会 (論文の主張・概念の定義) はこちら
- `trace-to-source`: コード ↔ 実装詳細のトレース
- 本スキルは「**主張ベース** (本研究の方針・設計判断)」の照合に特化
