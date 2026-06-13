#!/usr/bin/env bash
# 单 tmux 会话、单 GPU：按 Phase 1→4 串行跑完全部 manifest（47 runs）
#
# 用法:
#   bash experiments/v8_sota5_campaign/tmux_run_campaign_serial.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
exec bash experiments/v8_sota5_campaign/tmux_run_campaign.sh "$@"
