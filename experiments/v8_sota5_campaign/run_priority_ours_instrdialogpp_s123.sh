#!/usr/bin/env bash
# 优先：ours + instrdialog++ + seed 123 (v8_sota_5 champion config)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PRIORITY_CONFIG="configs/paper/v8_sota5_campaign/ours_multiseed/instrdialogpp__v8_sota_5__s123.yaml"
exec bash experiments/v8_sota5_campaign/run_priority_job.sh
