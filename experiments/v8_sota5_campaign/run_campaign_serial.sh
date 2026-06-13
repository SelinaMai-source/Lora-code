#!/usr/bin/env bash
# 单 GPU 串行执行四阶段战役（Phase 1→4，共 47 runs）
# 委托 run_campaign_phased.sh；保留此脚本名以兼容 monitor 自动重启。
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: bash run_campaign_serial.sh [phase ...]"
  echo "Order: phase1_priority(1) -> baselines(30) -> ablation(10) -> ours(6)"
  exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
exec bash experiments/v8_sota5_campaign/run_campaign_phased.sh "$@"
