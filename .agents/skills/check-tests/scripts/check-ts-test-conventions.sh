#!/usr/bin/env bash
# mb-analyzer の *.test.ts について、LLM の注意力に依存せず機械検証できる規約を一括チェックする。
# 失敗が 1 件でもあれば非 0 で終了。SKILL.md の Step 4 から呼ばれる前提。

set -uo pipefail

# リポジトリルート (このスクリプトからの相対) に移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"

TEST_DIR="mb-analyzer/tests"

if [[ ! -d "${TEST_DIR}" ]]; then
  echo "ERROR: ${TEST_DIR} not found (run from repo root or via SKILL.md Step 4)." >&2
  exit 2
fi

FAILED=0

echo "== Check 1: JSDoc 冒頭ブロック (/**) の存在 =="
# ai-guide/quality-check/mb-analyzer.md:59-92 の「テストファイル冒頭コメント」節を機械化。
while IFS= read -r -d '' file; do
  first_line="$(head -n 1 "${file}")"
  if [[ "${first_line}" != "/**" ]]; then
    echo "  MISSING header: ${file}"
    FAILED=1
  fi
done < <(find "${TEST_DIR}" -name "*.test.ts" -type f -print0 | sort -z)

if [[ ${FAILED} -eq 0 ]]; then
  echo "  OK (all *.test.ts have JSDoc header)"
fi

echo ""
echo "== Check 2: it.only / describe.only の残存 =="
# ai-guide/quality-check/mb-analyzer.md:229 の「コミット前に必ず戻す」を機械化。
ONLY_HITS="$(grep -rnE "^\s*(it|describe)\.only\(" "${TEST_DIR}" --include="*.test.ts" || true)"
if [[ -n "${ONLY_HITS}" ]]; then
  echo "  FOUND .only (remove before commit):"
  echo "${ONLY_HITS}" | sed 's/^/    /'
  FAILED=1
else
  echo "  OK (no .only residues)"
fi

echo ""
if [[ ${FAILED} -ne 0 ]]; then
  echo "FAILED: 上記の違反を修正してから次のステップに進んでください。"
  exit 1
fi
echo "PASSED: 全ての機械検証項目をクリア。"
exit 0
