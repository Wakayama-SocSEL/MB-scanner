#!/bin/bash
# worktreeのtmpをmainリポジトリに連番で保存する
# Usage: save-worktree-tmp.sh <work-name> <worktree-dir> <original-dir>

set -euo pipefail

WORK_NAME="${1:-}"
WORKTREE_DIR="${2:-}"
ORIGINAL_DIR="${3:-}"

if [[ -z "$WORK_NAME" ]] || [[ -z "$WORKTREE_DIR" ]] || [[ -z "$ORIGINAL_DIR" ]]; then
  echo "Usage: $(basename "$0") <work-name> <worktree-dir> <original-dir>" >&2
  exit 1
fi

SRC_DIR="$WORKTREE_DIR/tmp"
DEST_BASE="$ORIGINAL_DIR/tmp"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Error: worktreeにtmpディレクトリが存在しません: $SRC_DIR" >&2
  exit 1
fi

# 保存先ベースディレクトリを作成
mkdir -p "$DEST_BASE"

# 連番を計算
MAX_NUM=0
for dir in "$DEST_BASE"/[0-9][0-9][0-9][0-9]_*/; do
  if [[ -d "$dir" ]]; then
    NUM=$(basename "$dir" | grep -oE '^[0-9]+' || echo "0")
    NUM=$((10#$NUM))
    if (( NUM > MAX_NUM )); then
      MAX_NUM=$NUM
    fi
  fi
done
NEXT_NUM=$(printf "%04d" $((MAX_NUM + 1)))

# 作業名をファイル名に適した形式に変換
SAFE_NAME=$(echo "$WORK_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-_')

DEST_DIR="$DEST_BASE/${NEXT_NUM}_${SAFE_NAME}"

# コピー
cp -r "$SRC_DIR/." "$DEST_DIR"

echo "{"
echo "  \"saved_dir\": \"$DEST_DIR\","
echo "  \"sequence_number\": \"$NEXT_NUM\""
echo "}"
