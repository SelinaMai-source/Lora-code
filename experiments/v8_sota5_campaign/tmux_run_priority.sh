#!/usr/bin/env bash
# 启动优先任务 tmux 会话 v8s5camp_priority（单 GPU，仅一个 train.py）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SESSION="v8s5camp_priority"
SCRIPT="experiments/v8_sota5_campaign/run_priority_ours_instrdialogpp_s123.sh"

if pgrep -f "[p]ython.*core/train.py" >/dev/null 2>&1; then
  echo "错误: 已有 train.py 在运行，请先 pause_serial_for_priority.sh"
  pgrep -af "[p]ython.*core/train.py" || true
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux 会话已存在: $SESSION"
  echo "  连接: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" bash -lc "cd '$ROOT' && bash '$SCRIPT'"
echo "已启动优先任务 tmux: $SESSION"
echo "  配置: configs/paper/v8_sota5_campaign/ours_multiseed/instrdialogpp__v8_sota_5__s123.yaml"
echo "  连接: tmux attach -t $SESSION"
