#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

MONITOR_LOOP="experiments/lora_strict_campaign/supervisor/monitor_loop.sh"
AGENT_LOOP="experiments/lora_strict_campaign/supervisor/agent_loop.sh"

start_or_restart() {
  local session="$1"
  local cmd="$2"
  if tmux has-session -t "$session" 2>/dev/null; then
    tmux kill-session -t "$session"
    echo "[start_supervisor] restarted: $session"
  else
    echo "[start_supervisor] started: $session"
  fi
  tmux new-session -d -s "$session" "bash $cmd"
}

start_or_restart lora_strict_supervisor "$MONITOR_LOOP"
start_or_restart lora_strict_agent_loop "$AGENT_LOOP"

echo "[start_supervisor] active sessions:"
tmux ls 2>/dev/null | grep -E 'lora_strict_(supervisor|agent_loop)' || true
