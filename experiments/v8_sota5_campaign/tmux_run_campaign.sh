#!/usr/bin/env bash
# 单 tmux 会话、单 GPU：按 Phase 1→4 串行跑完全部 manifest（47 runs）
#
# 用法:
#   bash experiments/v8_sota5_campaign/tmux_run_campaign.sh
#   bash experiments/v8_sota5_campaign/tmux_run_campaign.sh 1   # 仅 Phase 1
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SESSION="v8s5camp_serial"
SCRIPT="experiments/v8_sota5_campaign/run_campaign_phased.sh"
EXTRA_ARGS=("$@")

if pgrep -f "[p]ython.*core/train.py" >/dev/null 2>&1; then
  echo "错误: 已有 train.py 在运行。请先停止或使用 tmux attach 查看现有会话。"
  pgrep -af "[p]ython.*core/train.py" || true
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux 会话已存在: $SESSION"
  echo "  连接: tmux attach -t $SESSION"
  exit 0
fi

CMD="cd '$ROOT' && bash '$SCRIPT'"
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=" $(printf '%q ' "${EXTRA_ARGS[@]}")"
fi
tmux new-session -d -s "$SESSION" bash -lc "$CMD"
echo "已在后台启动串行战役 tmux: $SESSION"
echo "  连接: tmux attach -t $SESSION"
echo "  顺序: Phase1(1) -> Phase2(30) -> Phase3(10) -> Phase4(6) = 47 runs"
