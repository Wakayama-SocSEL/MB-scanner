---
name: create-pr
description: 現在のブランチの変更内容を解析し、PRテンプレートに沿ったPull Requestを作成する
argument-hint: <ベースブランチ（省略時はmain）>
---

# create-pr スキル

現在のブランチの変更を分析し、`.github/pull_request_template.md` に沿ったPull Requestを `gh` コマンドで作成します。

## 使用方法

```
/create-pr [ベースブランチ]
```

ベースブランチを省略した場合は `main` を使用します。

## 実行手順

### Step 1: 状態の確認

以下を並列で実行し、PRに含まれる変更の全体像を把握する：

```bash
git status
git log --oneline main..HEAD
git diff main..HEAD --stat
```

- 未コミットの変更がある場合は「未コミットの変更があります。先に `/commit` してください」と伝えて中断する
- リモートにプッシュ済みか確認する：
  ```bash
  git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
  ```

### Step 2: 変更内容の分析

`git log main..HEAD` と `git diff main..HEAD` を読み、以下を判断する：

- **PRタイトル**: commitルールと同じ `<type>: <subject>` 形式。日本語で簡潔に（70文字以内）
- **概要**: 変更の目的と背景を1〜2文で
- **変更内容**: 主要な変更を箇条書き
- **テスト**: テストの追加・修正があれば記載
- **関連 Issue**: コミットメッセージやブランチ名から推測できれば記載

### Step 3: リモートへプッシュ

リモートブランチが未設定、またはローカルが先行している場合：

```bash
git push -u origin HEAD
```

### Step 4: PRの作成

`gh pr create` でPRを作成する。bodyは `.github/pull_request_template.md` の形式に従う：

```bash
gh pr create --base <ベースブランチ> --title "<type>: <subject>" --body "$(cat <<'EOF'
## 概要

<概要テキスト>

## 変更内容

- <変更1>
- <変更2>

## テスト

- <テスト内容>

## 関連 Issue

closes #<Issue番号 or 空欄>
EOF
)"
```

### Step 5: 結果の報告

作成されたPRのURLをユーザーに表示する。

## 注意事項

- 対話型ツールは使用しない（`gh pr create` のインタラクティブモードは使わない）
- 全てのコミット（最新だけでなく）を分析してPRの説明を作成する
- ドラフトPRにしたい場合はユーザーが引数で指定する（`--draft`）
