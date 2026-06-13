#!/usr/bin/env bash
# 停止 v8_sota / campaign / paper matrix 相关实验进程与 tmux 会话。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "[pause] stopping experiment tmux sessions..."
for sess in v8_sota_{1..20} sota_agent_loop sota_monitor paper-matrix v8s5camp_ablation v8s5camp_ours v8s5camp_baselines v8s5camp_serial v8s5camp_queue v8s5camp_priority; do
  if tmux has-session -t "$sess" 2>/dev/null; then
    echo "  kill-session: $sess"
    tmux kill-session -t "$sess" || true
  fi
done

# Catch any remaining v8_sota_* or v8s5camp_* sessions
if tmux ls 2>/dev/null | grep -E 'v8_sota_|v8s5camp_|sota_agent|sota_monitor|paper-matrix' >/dev/null; then
  tmux ls 2>/dev/null | awk -F: '/v8_sota_|v8s5camp_|sota_agent|sota_monitor|paper-matrix/ {print $1}' | while read -r sess; do
    echo "  kill-session: $sess"
    tmux kill-session -t "$sess" 2>/dev/null || true
  done
fi

echo "[pause] stopping train.py / run_paper_matrix processes..."
pkill -f "python.*core/train.py" 2>/dev/null || true
pkill -f "python3 core/train.py" 2>/dev/null || true
pkill -f "run_paper_matrix.py" 2>/dev/null || true
pkill -f "run_from_manifest.py" 2>/dev/null || true
pkill -f "run_ours_mini_ablation.py" 2>/dev/null || true

sleep 1
REMAINING="$(pgrep -af 'train\.py|run_paper_matrix|run_from_manifest' 2>/dev/null || true)"
if [ -n "$REMAINING" ]; then
  echo "[warn] some processes may still be running:"
  echo "$REMAINING"
else
  echo "[pause] no active training processes detected."
fi
