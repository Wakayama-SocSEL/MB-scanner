---
name: start-implementation
description: 実装開始時に作業計画とプロンプト履歴ファイルを作成し、管理する
disable-model-invocation: true
argument-hint: /start-implementation <作業の説明>
---

# 実装開始スキル

実装作業を開始する際に、構造化された作業ディレクトリを作成し、計画とプロンプト履歴を管理します。

## 使用方法

```
/start-implementation <作業の説明>
```

または、ファイル参照付き：

```
/start-implementation @file.md の内容を実装する
```

## 作業フロー

### Step 1: 作業ディレクトリの初期化

以下のスクリプトを実行して作業ディレクトリを作成してください：

```bash
.claude/skills/start-implementation/init-work-dir.sh "<作業名>" "$(pwd)/tmp"
```

**出力例:**
```json
{
  "work_dir": "/path/to/project/tmp/0001_feature-name",
  "plan_file": "/path/to/project/tmp/0001_feature-name/plan.md",
  "prompt_file": "/path/to/project/tmp/0001_feature-name/prompt.md",
  "sequence_number": "0001",
  "work_name": "feature-name"
}
```

### Step 2: コードベースの調査とファイルへの書き込み

[references/planning-prompt.md](references/planning-prompt.md) をプランニングのプロンプトとして参照し、Plan サブエージェントにコードベースの調査と実装計画の策定を委譲してください。

1. Plan サブエージェントにコードベースの調査を委譲する
2. `prompt.md` にユーザーからの指示を**そのまま**記録（加筆・修正は禁止）
3. Plan サブエージェントの調査結果をもとに `plan.md` に以下を記載：
   - 作業の概要と目的
   - 関連ファイルの調査結果
   - 実装計画（フェーズ分け、タスクリスト）
   - 懸念事項やリスク

### Step 3: ユーザー承認

**重要**: コード変更は勝手に実施してはいけません。

1. `plan.md` をユーザーに提示
2. 実装の許可を得る
3. 許可が得られるまでプランを調整

### Step 4: 実装と記録

許可後：
1. 計画に従って実装
2. ユーザーからの追加指示は `prompt.md` に追記
3. 実施内容も `prompt.md` に記録
4. 作業完了ごとに、型チェック、フォーマットの実施を行なってください。フォーマットは、変更ファイルに限定して実行してください。テストを実装した際は、変更したファイルのみが対象となるようにした上で実行してください。
   - フォーマット・Lint修正: `just fix`
   - 型チェック: `just typecheck`
   - テスト実行: `uv run pytest <対象ファイル>`

## prompt.md のフォーマット

```markdown
# プロンプト履歴

## 初回指示 (YYYY-MM-DD)

### ユーザーからの指示

{プロンプトをそのまま貼る}

### 実施内容

実施した内容を記載

---

## フィードバック 1 (YYYY-MM-DD)

### ユーザーからのフィードバック

{プロンプトをそのまま貼る}

### 実施内容

実施した内容を記載
```

## ヒント

- 作業ディレクトリは連番管理（0001, 0002, ...）で自動採番
- 作業名はハイフン区切りの小文字に正規化される
- 複数プロジェクトで使用可能（base-dir を指定）
