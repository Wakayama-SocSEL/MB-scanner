---
name: start-worktree
description: git worktreeで新しいフィーチャーブランチを作成し、just python-depsを実行後にcmuxの右ペインでClaudeを起動する。ブランチを切って実装を始めたい、worktreeでfeatureを開発したいときに使う。
argument-hint: <ブランチ名 または 実装したい機能の説明>
---

# start-worktree スキル

git worktreeで分離した作業環境を作り、cmuxの右ペインで新しいClaudeセッションを起動します。
計画・実装は起動後のセッション内で `/start-implementation` を使って行います。

## 使用方法

```
/start-worktree <ブランチ名 または 実装したい機能の説明>
```

## 作業フロー

### Step 1: ブランチ名の決定

引数がブランチ名の形式（英数字・スラッシュ・ハイフンのみ）であればそのまま使用する。
そうでなければ、引数の内容から適切なブランチ名を生成する（確認は取らない）：

- `feature/` / `fix/` / `chore/` / `refactor/` などのプレフィックスを判断して付ける
- 残りの部分は英語で簡潔なハイフン区切りにする（例: `add-auth`, `fix-login-bug`）

### Step 2: Worktreeの作成

```bash
.claude/skills/start-worktree/create-worktree.sh "<ブランチ名>"
```

JSONから `worktree_dir` / `original_dir` / `branch` を取得する。

### Step 3: cmuxで新しいClaudeセッションを起動

```bash
.claude/skills/start-worktree/open-in-cmux.sh "<worktree_dir>" "<original_dir>"
```

- `SETUP_COMMANDS`（`just python-deps`）実行後、Claudeが起動する
- 起動後のセッションで `/start-implementation` を使って計画・実装を行う

## 前提条件

- `cmux` がインストール済みであること
- `jq` がインストール済みであること
- cmux のウィンドウ内でスクリプトを実行すること
