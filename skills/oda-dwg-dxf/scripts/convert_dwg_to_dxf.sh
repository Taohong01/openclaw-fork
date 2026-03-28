#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $(basename "$0") <input_dir> <output_dir>" >&2
  exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

ODA_BIN="/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"

if [[ ! -x "$ODA_BIN" ]]; then
  echo "ODA File Converter not found or not executable at: $ODA_BIN" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

"$ODA_BIN" "$INPUT_DIR" "$OUTPUT_DIR" ACAD2018 DXF 1 0
