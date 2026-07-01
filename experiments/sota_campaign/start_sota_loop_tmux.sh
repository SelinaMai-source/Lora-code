#!/usr/bin/env bash
# One-command launcher: persistent tmux session `sota_loop` running the SOTA iteration supervisor.
set -euo pipefail
ROOT="/root/autodl-tmp/Lora-code"
SESSION="sota_loop"
LOOP="${ROOT}/experiments/sota_campaign/run_sota_iteration_loop.sh"

cd "$ROOT"
chmod +x "$LOOP"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session '$SESSION' already running. Attach: tmux attach -t $SESSION"
  exit 0
fi

rm -f "${ROOT}/experiments/sota_campaign/PAUSE_SOTA_ITERATION_LOOP"
tmux new-session -d -s "$SESSION" "bash -lc 'cd \"$ROOT\" && exec bash \"$LOOP\"'"
echo "Started tmux session: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Tail loop log: tail -f ${ROOT}/experiments/sota_campaign/logs/sota_iteration_loop.log"
