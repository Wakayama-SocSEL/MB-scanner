#!/usr/bin/env bash
# アーキテクチャ規約のうち、LLM の注意力に依存せず機械検証できる項目を一括チェックする。
# 既存ツール (import-linter / ESLint / pyright / tsc) でカバーできない範囲のみを対象とする。
# SKILL.md の Step 4 から呼ばれる前提。失敗があれば非 0 で終了。

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"

FAILED=0

echo "== Check 1: mb_scanner/domain/ に @dataclass / dataclasses 混入がないか =="
# ai-guide/architecture/mb-scanner.md: ドメイン層は Pydantic BaseModel のみで構成する規約。
if [[ -d mb_scanner/domain ]]; then
  HITS="$(grep -rnE "^\s*(from\s+dataclasses|import\s+dataclasses|@dataclass(\b|\())" mb_scanner/domain --include="*.py" || true)"
  if [[ -n "${HITS}" ]]; then
    echo "  VIOLATION (domain は Pydantic BaseModel のみ):"
    echo "${HITS}" | sed 's/^/    /'
    FAILED=1
  else
    echo "  OK"
  fi
else
  echo "  SKIP (mb_scanner/domain/ が存在しない)"
fi

echo ""
echo "== Check 2: mb_scanner/ でバッチ進捗用ライブラリ (tqdm / rich.progress) が import されていないか =="
# ai-guide/architecture/mb-scanner.md:172 — バッチ進捗は stderr の "[progress] N/total" 形式のみ。
# rich.console / rich.table 等の他用途は対象外 (GitHub CLI の表出力などで使用するため)。
if [[ -d mb_scanner ]]; then
  HITS="$(grep -rnE "^\s*(from\s+(tqdm|rich\.progress)|import\s+tqdm)" mb_scanner --include="*.py" || true)"
  if [[ -n "${HITS}" ]]; then
    echo "  VIOLATION (stderr 進捗表示規約違反):"
    echo "${HITS}" | sed 's/^/    /'
    FAILED=1
  else
    echo "  OK"
  fi
else
  echo "  SKIP (mb_scanner/ が存在しない)"
fi

echo ""
echo "== Check 3: 横断 JSON 契約: EquivalenceInput の extra=\"forbid\" 維持 =="
# ai-guide/architecture/index.md の JSON 契約節: 入力は厳格、出力は寛容の非対称設計。
CONTRACT_FILE="mb_scanner/domain/entities/equivalence.py"
if [[ -f "${CONTRACT_FILE}" ]]; then
  # EquivalenceInput クラスブロック内に extra="forbid" があるか
  INPUT_OK="$(awk '
    /^class EquivalenceInput\(/      { in_block=1; next }
    in_block && /^class /            { in_block=0 }
    in_block && /extra="forbid"/     { print "ok"; exit }
  ' "${CONTRACT_FILE}")"
  if [[ "${INPUT_OK}" == "ok" ]]; then
    echo "  OK (EquivalenceInput: extra=\"forbid\")"
  else
    echo "  VIOLATION: EquivalenceInput クラスに extra=\"forbid\" が見つからない (${CONTRACT_FILE})"
    FAILED=1
  fi

  RESULT_OK="$(awk '
    /^class EquivalenceCheckResult\(/ { in_block=1; next }
    in_block && /^class /             { in_block=0 }
    in_block && /extra="ignore"/      { print "ok"; exit }
  ' "${CONTRACT_FILE}")"
  if [[ "${RESULT_OK}" == "ok" ]]; then
    echo "  OK (EquivalenceCheckResult: extra=\"ignore\")"
  else
    echo "  VIOLATION: EquivalenceCheckResult クラスに extra=\"ignore\" が見つからない (${CONTRACT_FILE})"
    FAILED=1
  fi
else
  echo "  SKIP (${CONTRACT_FILE} が存在しない)"
fi

echo ""
if [[ ${FAILED} -ne 0 ]]; then
  echo "FAILED: 上記の違反を修正してから次のステップに進んでください。"
  exit 1
fi
echo "PASSED: 全ての機械検証項目をクリア。"
exit 0
