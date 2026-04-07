#!/bin/bash
# 品質ゲート: fix → typecheck → test を順次実行

# Stop hookが既にアクティブな場合はスキップ（無限ループ防止）
INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active')
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# ----------------------------------------
# 無限ループ防止用の設定
# ----------------------------------------
MAX_RETRIES=3 # 最大リトライ回数
TMP_DIR=".claude/tmp"
COUNT_FILE="$TMP_DIR/ci_loop_count"

mkdir -p "$TMP_DIR"
# カウンターファイルの読み込み（なければ0）
LOOP_COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo "0")

ERRORS=""

# ----------------------------------------
# 1. Ruff format/lintチェック
# ----------------------------------------
# ログをキャプチャしつつ実行
FIX_OUTPUT=$(just fix 2>&1)
if [ $? -ne 0 ]; then
  # 失敗した場合は、AIが直せるように実際のログも含める
  ERRORS="${ERRORS}【just fix のエラー】\n${FIX_OUTPUT}\n\n"
fi

# ----------------------------------------
# 2. 型チェック
# ----------------------------------------
# ログをキャプチャしつつ実行
TYPECHECK_OUTPUT=$(just typecheck 2>&1)
if [ $? -ne 0 ]; then
  # 失敗した場合は実際のログも含める
  ERRORS="${ERRORS}【just typecheck のエラー】\n${TYPECHECK_OUTPUT}\n\n"
fi

# ----------------------------------------
# 3. テスト実行
# ----------------------------------------
# ログをキャプチャしつつ実行
TEST_OUTPUT=$(uv run pytest 2>&1)
if [ $? -ne 0 ]; then
  # 失敗した場合は実際のログも含める
  ERRORS="${ERRORS}【uv run pytest のエラー】\n${TEST_OUTPUT}\n\n"
fi

# ----------------------------------------
# 結果の判定とClaudeへのフィードバック
# ----------------------------------------
if [ -n "$ERRORS" ]; then
  LOOP_COUNT=$((LOOP_COUNT + 1))

  # 規定回数を超えたら Exit 1 でループを断ち切る
  if [ "$LOOP_COUNT" -ge "$MAX_RETRIES" ]; then
    echo -e "🚨 $MAX_RETRIES 回連続でエラーが解決しませんでした。無限ループを防ぐため、人間の確認を待ちます。\n\n$ERRORS" >&2
    rm -f "$COUNT_FILE" # 次回手動で回すときのためにリセット
    exit 1 # Exit 1 はAIの自動リトライを発火させず、単にエラーとして停止する
  fi

  # 規定回数未満なら Exit 2 でAIに修正させる
  echo "$LOOP_COUNT" > "$COUNT_FILE"
  echo -e "❌ CIが失敗しました (試行: $LOOP_COUNT/$MAX_RETRIES)。以下のエラーを修正してください：\n\n$ERRORS" >&2
  exit 2
fi

# 成功した場合（エラーなし）はカウンターをリセットして正常終了
rm -f "$COUNT_FILE"
echo "✅ すべての品質ゲート（fix & test）を通過しました！"
exit 0
