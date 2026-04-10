#!/bin/bash
# 作業ディレクトリの初期化スクリプト
# Usage: init-work-dir.sh <work-name> [base-dir]

set -euo pipefail

WORK_NAME="${1:-}"
BASE_DIR="${2:-$(pwd)/tmp}"

if [[ -z "$WORK_NAME" ]]; then
  echo "Error: 作業名を指定してください" >&2
  echo "Usage: $0 <work-name> [base-dir]" >&2
  exit 1
fi

# base-dirが存在しない場合は作成
mkdir -p "$BASE_DIR"

# 既存ディレクトリから最大の連番を取得
MAX_NUM=0
if [[ -d "$BASE_DIR" ]]; then
  for dir in "$BASE_DIR"/[0-9][0-9][0-9][0-9]_*/; do
    if [[ -d "$dir" ]]; then
      NUM=$(basename "$dir" | grep -oE '^[0-9]+' || echo "0")
      NUM=$((10#$NUM))  # 先頭のゼロを除去して数値化
      if (( NUM > MAX_NUM )); then
        MAX_NUM=$NUM
      fi
    fi
  done
fi

# 次の連番を計算（4桁ゼロ埋め）
NEXT_NUM=$(printf "%04d" $((MAX_NUM + 1)))

# 作業名をファイル名に適した形式に変換（スペース→ハイフン、小文字化）
SAFE_NAME=$(echo "$WORK_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-_')

# 作業ディレクトリのパス
WORK_DIR="$BASE_DIR/${NEXT_NUM}_${SAFE_NAME}"

# ディレクトリを作成
mkdir -p "$WORK_DIR"

# 日付を取得
TODAY=$(date +%Y-%m-%d)

# plan.md を作成
cat > "$WORK_DIR/plan.md" << EOF
# 実行プラン: ${WORK_NAME}

作成日: ${TODAY}

## 概要

<!-- 作業の概要を記載 -->

## 目的

<!-- 達成したいゴールを記載 -->

## 調査結果

<!-- 関連ファイル、既存実装の調査結果 -->

## 実装計画

### Phase 1: 準備

- [ ] タスク1
- [ ] タスク2

### Phase 2: 実装

- [ ] タスク3
- [ ] タスク4

### Phase 3: テスト・検証

- [ ] タスク5

## 懸念事項・リスク

<!-- 考慮すべきリスクや懸念点 -->

## 備考

<!-- その他のメモ -->
EOF

# prompt.md を作成
cat > "$WORK_DIR/prompt.md" << EOF
# プロンプト履歴

## 初回指示 (${TODAY})

### ユーザーからの指示

<!-- ここに最初のプロンプトを記載 -->

### 実施内容

<!-- 実施した内容を記載 -->
EOF

# 結果を出力（JSON形式）
echo "{"
echo "  \"work_dir\": \"$WORK_DIR\","
echo "  \"plan_file\": \"$WORK_DIR/plan.md\","
echo "  \"prompt_file\": \"$WORK_DIR/prompt.md\","
echo "  \"sequence_number\": \"$NEXT_NUM\","
echo "  \"work_name\": \"$SAFE_NAME\""
echo "}"
