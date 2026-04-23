# アーキテクチャ・設計ガイド

## ai-guide 4 軸の住み分け

`ai-guide/` は用途別に 4 軸で構成されています。書きたい内容の語尾で振り分け、重複を避けてください:

| 文書 | 性質 | 文体 | 想定読者 |
|---|---|---|---|
| **`architecture/`** (本文書) | **Contract** — 〜すべき / 〜禁止 / 〜と一致 | 表・条件文 | `check-architecture` skill, レビュー時の自分 |
| [`quality-check/`](../quality-check/index.md) | **Process** — 〜を確認する / 〜で検証する | 手順書 | `check-tests` skill, QA |
| [`code-map.md`](../code-map.md) | **Reference** — 〜する仕組み / 〜のため〜 | 物語・図・データフロー | 論文執筆、onboarding |
| [`adr/`](../adr/README.md) | **Decisions** — 〜を採用し、〜を却下した | Context / 選択肢 / 決定 / トリガー | 設計判断を見直す人、履歴を追いたい人 |

**drift 防止**: 意味論的な詳細（オラクル責務・観測軸・verdict 合成など）は `code-map.md` に集約し、本文書からはリンクのみを置く。**矛盾時は architecture/ を正とする**（契約が優先）。ADR は採用判断の根拠を残すだけで、現行契約は必ず `architecture/` 側に反映する。

---

## プロジェクト概要

MB-Scanner は、GitHub 上の多数の JavaScript リポジトリに対して CodeQL クエリを体系的に実行し、さらに等価性検証器・Pruning・同値分割テストなどの AST ベース静的解析を組み合わせるバッチプラットフォームです。定量・定性的なデータセットを構築し、クエリの有効性を実世界のコードベースで検証することを目的としています。

## 構成

本プロジェクトは **Python 側 (`mb_scanner/`)** と **TypeScript 側 (`mb-analyzer/`)** の 2 つのコードベースから成ります。言語ごとに依存方向ルールと静的解析の体系が異なるため、以下の 2 文書で個別に詳細を扱います。

- [`mb-scanner.md`](mb-scanner.md) — Python 側の Clean Architecture 4 層、ドメインモデル、DB 設計、Python コーディング規約
- [`mb-analyzer.md`](mb-analyzer.md) — TypeScript 側の依存方向ゾーン、ESLint 機械強制、サンドボックス、TS 新機能の追加

本 index.md では両コードベースにまたがる **共通概念** のみを扱います。

---

## 共通のアーキテクチャ原則

### Clean Architecture (依存方向は常に内側に向かう)

両コードベースとも Clean Architecture を採用し、依存方向が外側 → 内側に向かう構造を取ります。

- **Python 側**: `domain → use_cases → adapters → infrastructure` の 4 層を `import-linter` で機械強制
- **TypeScript 側**: `shared → equivalence-checker → pruning → ... → cli` のゾーン構造を ESLint `import/no-restricted-paths` で機械強制

詳細な契約は言語別ドキュメント参照。

### 役割分担

- **Python 側 (`mb_scanner/`)**: GitHub 検索、SQLite 永続化、CodeQL CLI 連携、並列バッチ実行 (`ThreadPoolExecutor`)、CLI エントリポイント
- **TypeScript 側 (`mb-analyzer/`)**: AST 解析とサンドボックス実行を担う薄い CLI。Python 側から `dist/cli.js` を subprocess 起動して stdin/stdout の JSON で呼び出される

---

## コメントとドキュメントの層分離

コードとドキュメントに残す情報は「読み手が何をしたいか」で層を分けます。

| 読み手の目的 | 置き場所 |
|---|---|
| 関数を **使う** (契約・挙動を知る) | JSDoc (TS) / docstring (Python) |
| **自明でない局所的な工夫** を理解する | ソース内 `//` / `#` コメント |
| 採用判断を **変える** (却下した選択肢を見直す) | [`adr/`](../adr/README.md) |
| 日付軸のマイルストーン | `TODO.md` |

**判定基準**: 「読み手は *使う* 人か、*変える* 人か」。使う人向けなら JSDoc / docstring、変える人向けなら ADR。

### 具体原則

- **JSDoc / docstring は契約のみ**: 不変条件・前提・失敗条件を書く。採用理由や却下した選択肢は書かない (それは ADR の仕事)
- **`//` / `#` は自明でない時だけ**: 関数名とシグネチャから読み取れる内容は書かない
- **section divider コメント** (例: `// --- 内部ヘルパ ---`) は原則避ける。export 境界や関数分割で区切りは自明
- **ADR への参照**: `// 判断: ai-guide/adr/NNNN-xxx.md` 形式で 1 行。理由や却下案は ADR 側に
- **言葉使い**: 具体的に (「ms オーダで重い」のような未計測の誇張は避ける、計測値がなければ定性的に書く)

言語固有の書き方は [`mb-scanner.md`](mb-scanner.md) / [`mb-analyzer.md`](mb-analyzer.md) を参照。

---

## Python ↔ Node の JSON 契約

両コードベースをまたぐ通信は `subprocess` の stdin/stdout に載せた JSON/JSONL で行います。契約破りは静的解析で検出できないため、以下の規約を厳守します。

### フィールド命名

- **snake_case で統一**: Python 側 `EquivalenceInput.timeout_ms` ↔ TS 側 `EquivalenceInput.timeout_ms`
- **列挙値文字列も完全一致**: `"equal" / "not_equal" / "error"` など。片側だけ変更しない。

### スキーマ互換性

- **Python 側 `EquivalenceCheckResult` は `extra="ignore"`**: TS 側が将来フィールドを足しても壊れない
- **Python 側 `EquivalenceInput` は `extra="forbid"`**: 想定外の入力を早期失敗させる

### バッチ API の順序独立性 (`id` エコーバック)

- バッチ API では Python 側が `id: str` を付与、Node 側が結果にエコーバック
- Python ↔ Node 間で順序暗黙依存を持たず、`id` をキーにマッピングして復元する
- id 欠落の場合は Python 側で `line-NNNN` 等を自動補完

### 受け渡し乖離の検出 (`effective_timeout_ms`)

- Node の checker が実際に使った `timeout_ms` を結果にエコーバック
- Python Gateway が入力値と照合し、乖離していれば warning を `error_message` に注入
- 過去に Python→Node で `timeout_ms` がサイレントに DEFAULT=5000 にフォールバックした事例への多重防御

### JSON シリアライズ時の明示

- Python → Node へ送る際は `model_dump_json(exclude_defaults=False, exclude_none=False)` を明示
- 将来のリファクタで timeout_ms などがシリアライズから落ちる事故を防ぐ

---

## 新機能をどちら側に書くかの判断

| 機能の性質 | 実装先 |
|---|---|
| AST 解析、サンドボックス実行、ts-eslint ルール、ESTree 操作 | **TS (`mb-analyzer/`)** |
| GitHub API 連携、DB 永続化、並列実行、CLI エントリ | **Python (`mb_scanner/`)** |
| バッチのオーケストレーション、結果集約、ユーザー向け出力 | **Python** |
| 新しい oracle、sandbox の安定化処理 | **TS** |
| 両方にまたがる場合 | **TS に解析ロジック → Python が subprocess 呼び出し** のパターンを維持 |

迷ったら「Python は薄いオーケストレータ、TS は薄い CLI」の役割分担を崩さないことを優先します。

---

## 自動検証コマンド (両側)

```bash
mise run check              # 下記すべてを一括実行（CI と同等）
mise run check-arch         # Python: import-linter でレイヤー契約を検証
mise run typecheck          # Python: pyright 型チェック
mise run lint               # Python: ruff Lint
mise run typecheck-analyzer # TS: tsc --noEmit
mise run lint-analyzer      # TS: ESLint (依存方向検査込み)
mise run test               # Python: pytest
mise run test-analyzer      # TS: vitest
mise run build-analyzer     # TS: esbuild で dist/cli.js をバンドル (Python から利用する前に必要)
mise run fix                # Python: ruff format + ruff check --fix
```
