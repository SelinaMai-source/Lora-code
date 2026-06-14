#!/bin/bash
# Start or restart v8_sota5 campaign supervisor + agent_loop tmux sessions.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SUPERVISOR_LOOP="experiments/v8_sota5_campaign/supervisor/monitor_loop.sh"
AGENT_LOOP="experiments/v8_sota5_campaign/supervisor/agent_loop.sh"

start_or_restart() {
  local session="$1"
  local cmd="$2"
  if tmux has-session -t "$session" 2>/dev/null; then
    tmux kill-session -t "$session"
    echo "[start_supervisor] restarted tmux session: $session"
  else
    echo "[start_supervisor] started tmux session: $session"
  fi
  tmux new-session -d -s "$session" "bash $cmd"
}

start_or_restart v8s5camp_supervisor "$SUPERVISOR_LOOP"
start_or_restart v8s5camp_agent_loop "$AGENT_LOOP"

echo "[start_supervisor] tmux sessions:"
tmux ls 2>/dev/null | grep -E 'v8s5camp_(supervisor|agent_loop)' || true
