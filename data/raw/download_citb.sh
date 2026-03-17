#!/usr/bin/env bash
set -euo pipefail

echo "[CITB] Download scaffolding script"
echo
echo "This repository does NOT bundle the CITB benchmark."
echo "You must obtain CITB from the official source (paper / project page / authors)."
echo

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW_DIR="${ROOT_DIR}/data/raw"
TARGET_DIR="${RAW_DIR}/citb"

mkdir -p "${TARGET_DIR}/tasks" "${TARGET_DIR}/metadata" "${TARGET_DIR}/original_files"

cat <<'EOF'
Created:
  data/raw/citb/
    tasks/
    metadata/
    original_files/

Next steps (manual, because CITB access varies):
  1) Download CITB from the official provider.
  2) Place the downloaded files under data/raw/citb/original_files/.
  3) If CITB provides task splits, place them under data/raw/citb/tasks/.
  4) Put version/license notes under data/raw/citb/README_OR_LICENSE.txt.

IMPORTANT:
  - This script intentionally does NOT pretend to download CITB.
  - It only creates a safe, reproducible directory layout.

After you have raw data in place, use the preprocessing entry in core/data.py
to produce data/processed/ in the unified continual-stream format.
EOF

