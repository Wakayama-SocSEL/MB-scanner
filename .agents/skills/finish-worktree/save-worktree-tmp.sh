#!/bin/bash
# worktreeのtmpをmainリポジトリに連番で保存する
#
# 動作:
# - worktree の tmp/ 直下を走査し、^[0-9]{4}_ にマッチするディレクトリは
#   個別に main 側 tmp/ に再採番して mv する（元の slug は保持）
# - 連番にマッチしないファイル/ディレクトリが残っていれば、
#   それらをまとめて NNNN_<引数slug>/ という新しい連番ディレクトリに mv する
#
# Usage: save-worktree-tmp.sh <work-name> <worktree-dir> <original-dir>
# Output: {"saved_dirs": ["...", "..."]}

set -euo pipefail

WORK_NAME="${1:-}"
WORKTREE_DIR="${2:-}"
ORIGINAL_DIR="${3:-}"

if [[ -z "$WORK_NAME" ]] || [[ -z "$WORKTREE_DIR" ]] || [[ -z "$ORIGINAL_DIR" ]]; then
  echo "Usage: $(basename "$0") <work-name> <worktree-dir> <original-dir>" >&2
  exit 1
fi

# サブディレクトリが渡されても動くよう worktree トップに正規化
if [[ -d "$WORKTREE_DIR" ]]; then
  WORKTREE_TOP=$(git -C "$WORKTREE_DIR" rev-parse --show-toplevel 2>/dev/null || true)
  if [[ -n "$WORKTREE_TOP" ]]; then
    WORKTREE_DIR="$WORKTREE_TOP"
  fi
fi

SRC_DIR="$WORKTREE_DIR/tmp"
DEST_BASE="$ORIGINAL_DIR/tmp"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Error: worktreeにtmpディレクトリが存在しません: $SRC_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_BASE"

# 現在の main 側 tmp の最大連番を取得
get_max_num() {
  local max=0
  local dir num
  for dir in "$DEST_BASE"/[0-9][0-9][0-9][0-9]_*/; do
    [[ -d "$dir" ]] || continue
    num=$(basename "$dir" | grep -oE '^[0-9]+' || echo "0")
    num=$((10#$num))
    (( num > max )) && max=$num
  done
  echo "$max"
}

# 作業名をスラッグ化
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-_'
}

SAFE_NAME=$(slugify "$WORK_NAME")

# worktree 内 tmp の連番ディレクトリ・非連番アイテムを分類
NUMBERED_DIRS=()
LEFTOVER_ITEMS=()

shopt -s nullglob dotglob
for entry in "$SRC_DIR"/*; do
  base=$(basename "$entry")
  if [[ -d "$entry" && "$base" =~ ^[0-9]{4}_ ]]; then
    NUMBERED_DIRS+=("$entry")
  else
    LEFTOVER_ITEMS+=("$entry")
  fi
done
shopt -u nullglob dotglob

SAVED_DIRS=()
NEXT_NUM=$(($(get_max_num) + 1))

# 連番ディレクトリを個別に再採番して mv
# bash 3.x で空配列展開が unbound 扱いになるのを避けるため ${arr[@]+...} で防御
for src in ${NUMBERED_DIRS[@]+"${NUMBERED_DIRS[@]}"}; do
  base=$(basename "$src")
  # NNNN_xxx の xxx 部分を抽出（元の slug を保持）
  orig_slug="${base#????_}"
  new_name=$(printf "%04d_%s" "$NEXT_NUM" "$orig_slug")
  dest="$DEST_BASE/$new_name"
  mv "$src" "$dest"
  SAVED_DIRS+=("$dest")
  NEXT_NUM=$((NEXT_NUM + 1))
done

# 残ったアイテム（非連番）があれば、まとめて新しい連番ディレクトリへ mv
if (( ${#LEFTOVER_ITEMS[@]} > 0 )); then
  new_name=$(printf "%04d_%s" "$NEXT_NUM" "$SAFE_NAME")
  dest="$DEST_BASE/$new_name"
  mkdir -p "$dest"
  for item in ${LEFTOVER_ITEMS[@]+"${LEFTOVER_ITEMS[@]}"}; do
    mv "$item" "$dest/"
  done
  SAVED_DIRS+=("$dest")
  NEXT_NUM=$((NEXT_NUM + 1))
fi

# JSON 出力（saved_dirs 単一形式）
printf '{"saved_dirs":['
first=1
for d in ${SAVED_DIRS[@]+"${SAVED_DIRS[@]}"}; do
  if (( first )); then
    first=0
  else
    printf ','
  fi
  printf '"%s"' "$d"
done
printf ']}\n'
