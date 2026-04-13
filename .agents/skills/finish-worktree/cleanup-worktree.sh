#!/bin/bash
# worktree を削除し、可能なら cmux pane も close する
#
# 動作:
# 1. .cmux-surface を事前読み取り（worktree 削除後は読めなくなるため）
# 2. cwd を ORIGINAL_DIR に退避
# 3. git worktree remove
# 4. ベストエフォートで cmux close-surface
#    - 成功 → このプロセスごと消える
#    - 失敗 / .cmux-surface 無し → 完了メッセージを出して正常終了
#
# Usage: cleanup-worktree.sh <worktree-dir> <original-dir>

set -euo pipefail

WORKTREE_DIR="${1:-}"
ORIGINAL_DIR="${2:-}"

if [[ -z "$WORKTREE_DIR" ]] || [[ -z "$ORIGINAL_DIR" ]]; then
  echo "Usage: $(basename "$0") <worktree-dir> <original-dir>" >&2
  exit 1
fi

if [[ ! -d "$WORKTREE_DIR" ]]; then
  echo "Error: worktree ディレクトリが存在しません: $WORKTREE_DIR" >&2
  exit 1
fi

# サブディレクトリが渡されても動くよう worktree トップに正規化
WORKTREE_TOP=$(git -C "$WORKTREE_DIR" rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "$WORKTREE_TOP" ]]; then
  echo "Error: $WORKTREE_DIR は git worktree ではありません" >&2
  exit 1
fi
WORKTREE_DIR="$WORKTREE_TOP"

if [[ ! -d "$ORIGINAL_DIR" ]]; then
  echo "Error: original ディレクトリが存在しません: $ORIGINAL_DIR" >&2
  exit 1
fi

# Step 1: surface ID を削除前に読み取り
SURFACE=""
if [[ -f "$WORKTREE_DIR/.cmux-surface" ]]; then
  SURFACE=$(cat "$WORKTREE_DIR/.cmux-surface" 2>/dev/null || true)
fi

# Step 2: cwd を退避（呼び出し元の cwd 状態に依存しないため）
cd "$ORIGINAL_DIR"

# Step 3: worktree 削除（pre-flight 通過済み前提なので --force は付けない）
git worktree remove "$WORKTREE_DIR"

# Step 4: ベストエフォート pane close
PANE_CLOSED=0
if [[ -n "$SURFACE" ]]; then
  if command -v cmux >/dev/null 2>&1; then
    if cmux close-surface --surface "$SURFACE" 2>/dev/null; then
      PANE_CLOSED=1
    fi
  fi
fi

# ここまで来た = pane が閉じなかった or surface 情報なし
if (( PANE_CLOSED == 0 )); then
  echo "完了しました。この pane は手動で閉じてください。"
fi
