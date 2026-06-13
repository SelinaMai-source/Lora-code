#!/usr/bin/env bash
# 优先任务完成后恢复 v8s5camp_serial（--skip-existing 自动跳过已完成 run）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SESSION="v8s5camp_serial"
SCRIPT="experiments/v8_sota5_campaign/tmux_run_campaign_serial.sh"
PRIORITY_SESSION="v8s5camp_priority"

if pgrep -f "[p]ython.*core/train.py" >/dev/null 2>&1; then
  echo "[resume] BLOCKED: train.py still running"
  pgrep -af "[p]ython.*core/train.py" || true
  exit 1
fi

if tmux has-session -t "$PRIORITY_SESSION" 2>/dev/null; then
  echo "[resume] killing completed priority tmux session $PRIORITY_SESSION"
  tmux kill-session -t "$PRIORITY_SESSION" 2>/dev/null || true
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[resume] killing stale $SESSION tmux (will relaunch)"
  tmux kill-session -t "$SESSION" 2>/dev/null || true
fi

bash "$SCRIPT"
echo "[resume] relaunched $SESSION — baseline→ours→ablation with --skip-existing"
