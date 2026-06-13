#!/usr/bin/env bash
# baseline 已在 v8s5camp_baselines 中运行时，排队 ours + ablation（单 GPU 串行）
#
# 用法:
#   bash experiments/v8_sota5_campaign/tmux_run_campaign_queue_after_baselines.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SESSION="v8s5camp_queue"
SCRIPT="experiments/v8_sota5_campaign/run_campaign_queue_after_baselines.sh"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux 会话已存在: $SESSION"
  echo "  连接: tmux attach -t $SESSION"
  exit 0
fi

tmux new-session -d -s "$SESSION" bash -lc "cd '$ROOT' && bash '$SCRIPT'"
echo "已启动排队 tmux: $SESSION（等待 baselines 结束后跑 baselines -> ours -> ablation）"
echo "  连接: tmux attach -t $SESSION"
