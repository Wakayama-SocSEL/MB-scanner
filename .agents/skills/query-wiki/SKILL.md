---
name: query-wiki
description: ai-research-workspace の wiki を検索して引用付きで回答する。「SLACC の simion とは？」「EquiBench と HyClone の違いは？」「動的等価性検証の手法一覧」「この論文はどう主張している？」「どの会議を見るべき？」「どの論文を引くべき？」など、論文・概念・ドメイン事実の照会、文献サーベイ、引用元の確認に関わる文脈で必ずこのスキルを使う。明示的に呼ばれなくても、論文の主張や概念の定義を確認したい場面では自動でこのスキルを発火させること。ソースコード側 (MB-scanner 等) からも絶対パスで wiki を参照する
argument-hint: /query-wiki <質問文>
---

# query-wiki スキル

`~/dev/research/ai-research-workspace/wiki/` を検索し、引用付きで回答するスキル。
**workspace 外から呼ばれた場合**（MB-scanner など）も、絶対パスで wiki を参照する。

## 呼び出しパターン

- workspace 内: 相対パス `wiki/` を使う
- workspace 外: 絶対パス `~/dev/research/ai-research-workspace/wiki/` を使う

## 実行手順

### 1. 質問の意図を分解

質問からキーワードと求められている情報の種類を抽出：

- **事実照会**: 「SLACC の simion とは？」→ concept ページ or 論文ページを直接引く
- **対比**: 「EquiBench と HyClone の違いは？」→ 複数 paper ページを横断
- **サーベイ**: 「動的等価性検証の手法一覧」→ concept ページから関連論文を列挙
- **設計判断**: 「refuse-based soundness の根拠は？」→ my-research/current.md + 関連 concept

### 2. wiki を検索

以下の順に Grep / Read する：

1. `wiki/index.md` で全体構造を確認
2. `wiki/concepts/*.md` から該当概念ページを特定（Grep でキーワード一致）
3. `wiki/papers/*.md` から該当論文ページを特定
4. 必要なら `my-research/current.md` も参照（主張・設計判断を問われた場合）

**質問が「どこを探せばよいか」「どの会議を見るべきか」「どの論文を引くべきか」型の場合は，以下の meta reference を必ず参照する**:

- `ai-guide/venues.md` — 探索対象の学会・ジャーナル一覧 (Tier 0 SE / Tier 1 PL / Tier 2 補助)
- `wiki/reference-strategy.md` — 論文の引用カテゴリ × 必須論文 × ソース venue の対応表，および「即追加すべき論文」リスト

### 3. 回答を合成

以下の形式で回答する：

```markdown
## 回答
<質問への直接の答え>

## 根拠
- [wiki/papers/slacc.md](...) §主要貢献より: "..."
- [wiki/concepts/equivalence-checking.md](...) §動的アプローチより: "..."

## 関連ページ
- [[wiki/concepts/code-clone-detection]]
- [[wiki/papers/equibench]]

## 不確実性・抜け
<wiki に載っていない情報、矛盾する主張などがあれば明示>
```

### 4. file:line 引用

Claude Code で クリック可能な形式 `wiki/papers/slacc.md:42` を使う。ユーザーが即座にジャンプできる。

## 回答ポリシー

- **wiki に書いてあることだけを事実として述べる**。wiki に無い情報は「wiki に記載なし」と明示
- 論文の主張と my-research の主張を**混同しない**（「SLACC は X と主張」vs「本研究は X と主張」を区別）
- 矛盾する主張がある場合は両方提示
- 該当情報が薄ければ `ingest-paper` で追加するよう提案

## 注意事項

- `wiki/` 全体を無差別に Read しない（トークン消費）。まず Grep で絞る
- 質問が wiki の範囲を超える（実装詳細・コード）場合は `trace-to-source` skill を呼ぶよう誘導
