---
name: finish-worktree
description: worktree内での作業が完了した後、tmpディレクトリ（plan.md・prompt.md）をmainリポジトリへ移管し、worktreeを削除して後片付けする。コミットは /commit スキルで事前に済ませておくこと。
argument-hint: <作業スラッグ>
---

# finish-worktree スキル

worktree内の作業完了後に後片付けを行います。
コミット・プッシュは `/commit` スキルで事前に完了させてから実行してください。

## 使用方法

```
/finish-worktree <作業スラッグ>
```

作業スラッグは `start-worktree` で使用したブランチ名のスラッシュ以降の部分です（例: `add-auth`）。

## 前提条件

- コミット・プッシュが完了していること（`/commit` スキル使用）
- `ORIGINAL_REPO_DIR` 環境変数が設定されていること（`open-in-cmux.sh` が自動設定）
- `jq` がインストール済みであること

## 作業フロー

### Step 1: tmpをmainリポジトリへ移管

```bash
"$ORIGINAL_REPO_DIR/.claude/skills/finish-worktree/save-worktree-tmp.sh" \
  "<作業スラッグ>" \
  "$(pwd)" \
  "$ORIGINAL_REPO_DIR"
```

JSONから `saved_dir` / `sequence_number` を取得して保存先を確認する。

### Step 2: worktreeを削除

worktreeディレクトリのパスを取得してから削除する：

```bash
WORKTREE_DIR="$(pwd)"
cd "$ORIGINAL_REPO_DIR"
git worktree remove "$WORKTREE_DIR"
```

**注意**: `git worktree remove` は元リポジトリ側から実行する必要があるため、先に `cd` する。

### Step 3: cmuxペインを閉じる

`.cmux-surface` に保存された surface ID を読み込んでペインを閉じる：

```bash
SURFACE=$(cat "$WORKTREE_DIR/.cmux-surface")
cmux close-surface --surface "$SURFACE"
```

このコマンドでペイン（およびこのセッション）が終了する。

## 完了後

- `$ORIGINAL_REPO_DIR/tmp/` 以下に plan.md と prompt.md が連番で保存される
- worktree ディレクトリが削除される
- cmux ペインが閉じてセッションが終了する
