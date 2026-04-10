#!/bin/bash
# datamodel-codegenを実行してPydantic v2モデルを生成する
# Usage: run-codegen.sh <input-file>
# Output: /tmp/generated_model.py

set -euo pipefail

INPUT_FILE="${1:-}"

if [[ -z "$INPUT_FILE" ]]; then
  echo "Usage: $(basename "$0") <input-file>" >&2
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: ファイルが存在しません: $INPUT_FILE" >&2
  exit 1
fi

datamodel-codegen \
  --input "$INPUT_FILE" \
  --input-file-type json \
  --output-model-type pydantic_v2.BaseModel \
  --output /tmp/generated_model.py \
  --use-annotated \
  --field-constraints \
  --target-python-version 3.12

echo "/tmp/generated_model.py"
