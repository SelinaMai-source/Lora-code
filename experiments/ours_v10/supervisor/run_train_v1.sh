#!/bin/bash
# Launch Ours v10 v1 Seq-GLUE training (single shot for tmux train session).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

VERSION="${OURS_V10_VERSION:-1}"
CONFIG="experiments/ours_v10/configs/ours_v10_${VERSION}__seqglue__s123.yaml"
LOG="results/logs/ours_v10_v${VERSION}_seqglue_s123.log"

mkdir -p results/logs archives/ours_v10/v${VERSION}
cp "$CONFIG" "archives/ours_v10/v${VERSION}/config.yaml"
cp experiments/ours_v10/NOVELTY_v${VERSION}.md "archives/ours_v10/v${VERSION}/NOVELTY.md" 2>/dev/null || true

python3 scripts/ours_v10_sota_gap_audit.py

export OURS_V10_EARLY_STOP=1
echo "[$(date)] Starting ours_v10 v${VERSION} Seq-GLUE" | tee "$LOG"
exec python3 core/train.py --config "$CONFIG" 2>&1 | tee -a "$LOG"
