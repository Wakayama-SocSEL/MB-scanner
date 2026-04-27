# code-map — 実装の意味論リファレンス

この文書は **実装がどう動いているか**（データフロー、責務分担、内部不変条件）を説明する**リファレンス**です。論文執筆時の引用元、深堀り時の参照、新メンバ onboarding を主な用途とします。

## ai-guide 内での位置づけ

`ai-guide/` は 3 軸で構成されています。書きたい内容の語尾で振り分けてください:

| 文書 | 性質 | 想定文体 | 読者 |
|---|---|---|---|
| [`architecture/`](architecture/index.md) | **Contract**（〜すべき／〜禁止／〜と一致） | 表・条件文 | skill, レビュー時の自分 |
| [`quality-check/`](quality-check/index.md) | **Process**（〜を確認する／〜で検証する） | 手順書 | skill, QA |
| [`code-map.md`](code-map.md)（本文書） | **Reference**（〜する仕組み／〜のため〜） | 物語・図・データフロー | 論文執筆、onboarding |

**矛盾時の優先順位**: 契約が正、リファレンスは補足。本文書と `architecture/` の記述が食い違う場合は `architecture/` 側を信じてください。

---

## 目次

- [等価性検証器](#等価性検証器)
  - [観測軸: slow/fast と pre/post](#観測軸-slowfast-と-prepost)
  - [4 オラクルの責務分担](#4-オラクルの責務分担)
  - [オラクル間の排他ルールと `not_applicable` の意義](#オラクル間の排他ルールと-not_applicable-の意義)
- [Pruning エンジン](#pruning-エンジン)
  - [データフロー](#データフロー)
  - [候補ノード決定の 3 段フィルタ](#候補ノード決定の-3-段フィルタ)
  - [置換操作の粒度 (削除 vs ワイルドカード化)](#置換操作の粒度-削除-vs-ワイルドカード化)
  - [pruning の正確性 — 多層防御](#pruning-の正確性--多層防御)
  - [文法由来 blacklist の網羅性](#文法由来-blacklist-の網羅性)

（sandbox パイプライン / verdict 合成 / Python↔Node JSON 往復 の詳細は今後追加予定）

---

## 等価性検証器

### 観測軸: slow/fast と pre/post

等価性検証は **2 つの直交する軸** で観測を組み立てます。名前の由来が異なるので混同しないこと。

#### slow / fast 軸 ← データセット起源

Selakovic 2016 dataset の **before/after パッチペア** に対応します。1 トリプル = **(setup, slow=before, fast=after)** を同一 setup 上で別 sandbox 実行し、**検証したい意味論的差異はこの軸で現れる**のが研究目的上の要請です。

#### pre / post 軸 ← Oracle 2 の実装技法

JS の破壊的変更（`arr.push(x)` 等）は戻り値にも例外にも現れないため、`argument-mutation` oracle は body 実行の **直前 (pre) と直後 (post) の 2 回スナップショット** を取って差分から in-place mutation を検出します。**1 回の sandbox 実行内で閉じた時間軸** であり、slow/fast のサイド軸とは別概念です。

#### 2 軸の組み合わせ

```
               pre (body 前)       post (body 後)
slow サイド    slow.snapshots.pre  slow.snapshots.post
fast サイド    fast.snapshots.pre  fast.snapshots.post
```

- Oracle 2 は **`slow.post` vs `fast.post`** を比較する
- `pre` は不変条件の記録用（setup 共通性から `slow.pre == fast.pre` が想定される）
- `slow.pre != fast.pre` や key 集合の片側欠落は **setup 不変条件の違反** に当たるが、現状は防御的に `not_equal` に畳まれる

---

### 4 オラクルの責務分担

JS で観測可能な差異は 4 方向に落ち、各オラクルが 1 軸ずつ担当します。

```
body 実行
├─ 戻り値として出てくる       → O1 (return_value)
├─ 引数が破壊的に変わる        → O2 (argument_mutation)
├─ 例外として throw される      → O3 (exception)
└─ 外界に漏れ出す (console / global) → O4 (external_observation)
```

| # | Oracle | 比較対象 | 比較方法 | 実装 |
|---|---|---|---|---|
| O1 | `return_value` | body の**戻り値** | serialize 済み文字列の完全一致 | `oracles/return-value.ts` |
| O2 | `argument_mutation` | setup 由来 object/array の **body 後の状態** | key 毎に `slow.post` vs `fast.post` を比較 | `oracles/argument-mutation.ts` |
| O3 | `exception` | body が投げた**例外** | `ctor` + `message` の一致 | `oracles/exception.ts` |
| O4 | `external_observation` | **console 呼び出し列** + **新規 global 変数** | console: method/args の順序込み／globals: key 集合 | `oracles/external-observation.ts` |

#### O1: `return_value`

`slow.return_value` vs `fast.return_value`（`snapshotValue` で文字列化済み）を比較します。代表的な検出対象: `for..in` の列挙結果、`String()` の文字列化結果、Promise の解決値（`await` 後の値で比較）。

#### O2: `argument_mutation`

setup で定義された object/array 変数の **body 実行後スナップショット** を両サイドで突き合わせます。代表的な検出対象: `arr.push(x)`、`obj.key = v`、`splice` 等の in-place 破壊的変更。戻り値に現れない副作用を担当します。詳細は [観測軸セクション](#観測軸-slowfast-と-prepost) 参照。

#### O3: `exception`

`ExceptionCapture = { ctor: string, message: string }` を両サイドで突き合わせます。代表的な検出対象: prototype 汚染下での `TypeError`、`hasOwnProperty` が破壊された時の throw、実装差による例外メッセージ変化。

##### 限界と判断根拠

O3 は設計上 3 つの観測を **していない**。それぞれの判断を明記しておく（偽陽性・偽陰性の議論で参照されやすいため）。

| 非観測項目 | 判定 | 根拠 |
|---|---|---|
| stack trace の比較 | **要件（比較しない）** | パッチ適用で行番号・内部関数名は必ず変わる。stack を比較すると Selakovic の全パッチが `not_equal` になり、検証器として成立しない。**「意味論的等価性の定義に stack を含めない」** は設計要件であり妥協ではない |
| message 内の動的値（変数名・プロパティ名）に由来する揺れ | **許容（偽陽性にならない）** | (setup, slow, fast) は **同一プロセス・同一 V8 realm** で実行され、setup が共通なら埋め込まれる動的値も両側で一致する。V8 バージョン差による文言書き換え（例: `"Cannot read property"` → `"Cannot read properties of"`）は CI の Node バージョン固定 (`mise`) で対処する |
| 例外発生までの中間状態 | **限界ではない（O2/O4 で補完済み）** | `executor.ts:82-90` は try/catch 通過後に post snapshot / console 列を確定するため、throw 直前までの副作用は **O2 (arg_snapshots) / O4 (console_log, new_globals) が自動的に拾う**。O3 単体で partial state が見えない点は oracle 間の協調で解決済み |

**結論: O3 の設計上の非観測はすべて許容しうる。** 特に stack trace 非比較は「**意味論的等価性の定義上 stack を含めない**」という研究上の要件であり、拡張して比較可能にしても FP が爆発するだけなので採用しない。

#### O4: `external_observation`

2 つの副作用ストリームを比較します:

1. **`console_log`**: console.log/warn/error 等の呼び出し列 — **method 名 + 引数の順序込み**で完全一致
2. **`new_globals`**: body 実行中に新規作成された global 変数名の集合（順序無関係、`Set` 比較）

代表的な検出対象: デバッグ出力の意図しない削除、global への無名リーク（`var`/`let` 忘れ）、DOM/I/O 系パターンの副作用差分。

---

### オラクル間の排他ルールと `not_applicable` の意義

4 軸は独立に判定されるが、**Oracle 間で責務の押し付け合いが発生しないよう排他ルールが組み込まれている**。

#### ルール 1: 例外時は O1 が身を引く

`oracles/return-value.ts` L18-20:

```ts
if (slow.exception !== null || fast.exception !== null) {
  return { oracle, verdict: ORACLE_VERDICT.NOT_APPLICABLE };
}
```

片方でも例外が起きた瞬間、O1 は `not_applicable` を返して **例外の比較は O3 に完全委譲** する。これが無いと「例外の文字列表現 vs 正常値」を比較して偽陽性が出る。

#### ルール 2: `not_applicable` は overall verdict を潰さない

`deriveOverallVerdict` は observation のうち `not_applicable` を除外してから集約する。これにより、**該当しない軸の存在が overall verdict のノイズにならない**。

具体例:

- 両側とも同じ値を返す純粋関数 → O1 `equal`、O2-O4 `not_applicable`、overall `equal`
- 両側とも同じ例外を投げる関数 → O1 `not_applicable`、O3 `equal`、overall `equal`

`not_applicable` は「検査しない」ではなく「**この軸ではこのトリプルを判定しない（他軸に任せる）**」という**責務移譲のシグナル**として機能している。

#### ルール 3: overall verdict の合成優先順位

`deriveOverallVerdict`（`verdict.ts`）は以下の優先順位で合成する:

1. いずれかの oracle が `not_equal` → **`not_equal`**
2. いずれかの oracle が `error` → **`error`**
3. 全 oracle が `not_applicable` → **`error`**（観測対象ゼロでは等価性を判定できない）
4. 残りは少なくとも 1 つ `equal` を含む → **`equal`**

設計上の含意:

- **`not_equal` が最強**: 実際に差異が観測されたら、他軸で error や not_applicable が出ていても **not_equal を信じる**。「観測できた非等価」は「観測できなかった軸」より優先。
- **`error` は not_equal に負ける**: シリアライズ不能 (循環参照) や timeout 等で観測不可でも、別の軸で差異が取れていれば non-equivalent 判定を優先する。
- **全 not_applicable も error**: 「4 軸すべてで何も観測できなかった」は等価の証拠にはならず、**観測失敗**として扱う。例: 両側とも body が文のみ (return 無し、副作用なし、例外なし、引数変更なし)。

---

### 観測できない事象（既知の限界）

4 オラクルを揃えても、以下 4 件は観測対象外であり **偽陰性（non-equivalent を equal と誤判定）のリスク源**となる。本データセット (Selakovic 2016) では発生頻度が低く実害は限定的だが、**等価性検証器を汎用ツールとして他研究へ再利用する場合は拡張が必要**。

| # | 観測されない事象 | 原因（実装箇所） | Selakovic での影響度 |
|---|---|---|---|
| 1 | setup で定義された **primitive 変数の最終値** | `executor.ts:50-59` は `typeof val === "object"` の変数のみ trackedKeys に入れる。number / string / boolean は post snapshot の対象外 | **低** — Selakovic パターンは collection 操作主体で、カウンタ変数等の primitive 変更は稀 |
| 2 | body で新規作成された **global 変数の値** | `external-observation.ts:50-54` は `new_globals` のキー集合のみ比較。値は比較しない | **中** — `var` 忘れ等の global リークはあるが、値の差まで問題になる例は少ない |
| 3 | body 同期終了**後**に実行される非同期タスク | sandbox は body 同期完了で観測打ち切り。`setTimeout` / `queueMicrotask` / 未解決 Promise の副作用は見えない | **低** — Selakovic パターンは同期コード主体 |
| 4 | `null` で初期化された変数の **null → object 変化** | `executor.ts:55` の `val !== null` により、setup で null の場合は trackedKeys に入らない。body で object 化されても pre snapshot が無く不完全 | **非常に低** — setup で null を置く使い方はほぼ無い |

#### 判断と対処

- **本論文の範囲では修正不要**: Selakovic dataset で穴 1〜4 が踏まれる頻度は低く、RQ1（C1〜C4 の ablation）と事前分析（10 パターン自動導出 ≈100%）の主張を脅かさない。等価性検証器は**研究成果ではなく中間ツール**なので、検出されるべき差異を取り逃さない限り研究は成立する
- **検証器を他研究で再利用する場合は拡張を検討**: 特に #1 (primitive tracking) と #2 (new_globals 値比較) は素直な拡張で塞げる。#3 の非同期対応は sandbox の大規模改修が必要
- **論文の妥当性の脅威には 1 行で明示**: `current-research.md` §妥当性の脅威に「等価性検証器の観測範囲は object/array mutation / 戻り値 / 例外 / console+globals key に限定される」旨を記載する
- **Future Work に予約**: 穴 1〜4 を塞いだ一般化検証器を候補として残す

---

## Pruning エンジン

第 1 段階 (構造パターン導出) の本体。`(slow, fast, setup)` トリプルから **ワイルドカード付きの最小構造パターン** を出力する。実装は `mb-analyzer/src/pruning/` 配下。研究方針は [`current-research.md` §第 1 段階](current-research.md#第-1-段階-実行ベース-hydra-式-pruning) を参照。

### データフロー

```
PruningInput (slow, fast, setup, timeout_ms, max_iterations)
       ↓
    parse (slow & fast)                          ← ast/parser.ts
       ↓
    checkEquivalence(setup, slow, fast)          ← 初回検証 (等価性検証器を直接呼ぶ)
       ├─ not_equal → verdict = initial_mismatch で終了
       ├─ error     → verdict = error で終了
       └─ equal     ↓
    SubtreeDiff(slow, fast)                      ← ast/diff.ts: fast 側の全サブツリー hash
       ↓
    loop (max_iterations / total_budget_ms まで):
       enumerateCandidates(slow, diff)           ← ast/candidates.ts: 3 段フィルタ + size 降順
       for 各候補 (先頭から):
         replaceNode → generate → parse          ← ast/replace.ts: 1 箇所書き換え + round-trip
         checkEquivalence(setup, slow', fast)    ← L4 validation
         ├─ equal  → AST 更新 + placeholder 記録 → 次ループで再列挙
         └─ その他 → 必須ノード扱い (WeakSet に記録)
       ↓
    PruningResult (pattern_ast, pattern_code, placeholders, iterations)
```

### 候補ノード決定の 3 段フィルタ

`enumerateCandidates` は以下の条件をすべて満たすノードに限定する。

| # | フィルタ | 目的 | 実装 |
|---|---|---|---|
| 1 | 型 whitelist | pruning 可能な AST 型 (Statement / Expression / Identifier の 3 分類) のみ残す | `pruning/constants.ts` の `NODE_CATEGORY` keys |
| 2 | 親子位置 blacklist | 親 field validator が置換後の型を受理しない位置を**文法由来で自動判定**し除外 (ADR-0005) | `pruning/ast/grammar-blacklist.ts` の `getGrammarBlacklist()` |
| 3 | AST 差分フィルタ | fast に同型ノードが存在する「共通ノード」のみに絞る (差分ノードは必須扱いで保護) | `pruning/ast/diff.ts` の `SubtreeDiff.isCommon` |

`NODE_CATEGORY` は「候補型の分類」と「置換モードの選択」の両方を単一の真実の源泉にするためにモジュール直下に置いている (`engine.ts` の `modesForNode` もここから派生)。新しい型を pruning 対象に加えるときは `constants.ts` の 1 エントリ更新で両者に反映される。

### 置換操作の粒度 (削除 vs ワイルドカード化)

候補ノードの category で置換モードが 1:1 に決まる (`engine.ts` の `MODE_BY_CATEGORY`)。**「削除」と呼べる操作は statement カテゴリへの `EmptyStatement` 置換のみ** で、最小粒度は 1 Statement ノード。

| カテゴリ | 置換モード | 置換後 | 操作の意味 |
|---|---|---|---|
| statement | `deleteStatement` | `EmptyStatement` (`;`) | **削除** |
| identifier | `wildcardIdentifier` | `$VAR` (Identifier) | ワイルドカード化 (任意の識別子) |
| expression | `wildcardExpression` | `$Pn` (StringLiteral) | ワイルドカード化 (任意の式) |

statement カテゴリは `IfStatement` / `ExpressionStatement` / `VariableDeclaration` / `BlockStatement` / `ReturnStatement` / `ThrowStatement` の 6 型 (`constants.ts:NODE_CATEGORY`)。Statement 未満の粒度 (式単独や宣言の一部) は「削除」できず、必ず wildcard 化される。

ただし `body: [s1, s2, s3]` のような Statement 配列では `replaceNode` の `listIndex` 指定で 1 要素だけ `EmptyStatement` 化できるので、**隣接 Statement を残したまま 1 個ずつ削除する** ことは可能 (`replace.ts:applyReplacement`)。

### pruning の正確性 — 多層防御

候補置換が「文法的・意味論的に不正」になる経路は **4 層の validation で段階的に排除** される。

| 層 | チェック内容 | 実装箇所 | 失敗時の挙動 |
|---|---|---|---|
| L1 | 静的除外 (文法由来 blacklist) | `@babel/types` の `NODE_FIELDS`/`NODE_UNION_SHAPES__PRIVATE` から自動導出したカテゴリ別ルール (ADR-0005) | 候補リストから事前除外 (試行コスト削減) |
| L2 | Babel 型検査 | AST ビルダー (`identifier()`, `stringLiteral()` 等) が型不整合を throw | `replaceNode` が null → スキップ |
| L3 | round-trip 検証 | 置換後 AST を generate → parse で復元可能性を確認 | parse 失敗 → null → スキップ |
| L4 | 意味論的等価性 | `checkEquivalence` を sandbox 実行 | `not_equal` / `error` → 必須ノード扱い |

**L1 は効率化最適化に過ぎず、正確性は L2〜L4 の積で担保される**。L1 が漏れていても誤 prune (unsound な縮小) は発生せず、未除外の試行が sandbox 実行まで到達して L4 で弾かれるだけ (コストが増えるのみ)。

### 文法由来 blacklist の網羅性

L1 blacklist は `@babel/types` の `NODE_FIELDS[parent][key].validate` introspection (`oneOfNodeTypes` / `chainOf` / `NODE_UNION_SHAPES__PRIVATE`) から起動時 1 回だけ計算される (ADR-0005; `grammar-blacklist.ts`)。ルールは 3 カテゴリ (statement / identifier / expression) 別に、親 × 子位置で自動生成される。

カバーされる位置の例 (列挙は自動):

- **LVal 位置**: `ForIn/OfStatement.left`, `AssignmentExpression.left`, `VariableDeclarator.id`, `CatchClause.param`
- **Identifier-only 位置**: `MemberExpression.property (computed=false)`, `Object/ClassProperty/Method.key (computed=false)`, `Labeled/Break/ContinueStatement.label`, `Function*.id`, `Function*.params`
- **destructuring LVal**: `RestElement.argument`, `ArrayPattern.elements`, `ObjectPattern.properties`
- **module / TS 系**: `ImportSpecifier` / `ExportSpecifier` 識別子、`PrivateName`、`TSTypeAnnotation` — `NODE_CATEGORY` にない型は候補 whitelist 段階で既に弾かれるが、将来拡張時にも自動で L1 が追従する

**唯一の意図的 diff**: `UpdateExpression.argument` は旧手書き blacklist では除外していたが、文法上は `Expression` alias を受理するため自動導出では除外しない。意味論的に誤った prune は L4 等価性検証で弾く方針 (詳細は ADR-0005)。

論文上の扱い:

- pruning 候補除外は「**効率最適化**」として位置づけ、unsoundness の議論とは独立に扱う ([`current-research.md` §Unsoundness の緩和](current-research.md#第-1-段階-実行ベース-hydra-式-pruning) の 3 点目)
- blacklist は Selakovic dataset に依存せず `@babel/types` の文法メタデータから mechanically 導出される、と明言できる (dataset leak 回避)
