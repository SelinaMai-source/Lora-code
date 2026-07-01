#!/usr/bin/env bash
# Launch sota-v1 single-seed experiment in tmux session sota-v1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
CONFIG="configs/paper/sota_campaign/sota_v1_instrdialogpp_s123.yaml"
LOG="results/logs/paper_instrdialogpp_sota_v1_ours_s123.log"
SESSION="sota-v1"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session $SESSION already exists"
  exit 1
fi

mkdir -p results/logs
tmux new-session -d -s "$SESSION" "cd '$ROOT' && python3 core/train.py --config '$CONFIG' 2>&1 | tee '$LOG'"
echo "Started $SESSION -> $LOG"
