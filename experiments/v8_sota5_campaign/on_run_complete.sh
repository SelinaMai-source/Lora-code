#!/usr/bin/env bash
# 单 run 完成回调：读取 final_metrics.json，触发 agent wake（Phase 1 优先任务完成后调用）。
#
# Usage:
#   bash on_run_complete.sh --run-name paper_instrdialogpp_v8_sota5_ours_s123_v8s5camp --phase 1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUN_NAME=""
PHASE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2 ;;
    --phase) PHASE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash on_run_complete.sh --run-name <name> [--phase N]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "Missing --run-name" >&2
  exit 1
fi

SUPERVISOR_DIR="experiments/v8_sota5_campaign/supervisor"
WAKE_SCRIPT="${SUPERVISOR_DIR}/cursor_agent_wake.sh"
FINAL_METRICS="$ROOT/results/runs/$RUN_NAME/final_metrics.json"
LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/on_complete_$(date +%Y%m%d_%H%M%S).log"

python3 - "$RUN_NAME" "$FINAL_METRICS" "$PHASE" "$LOG_FILE" <<'PY'
import json, sys
from pathlib import Path

run_name, metrics_path, phase, log_file = sys.argv[1:5]
metrics_path = Path(metrics_path)
metrics = {}
if metrics_path.is_file():
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        pass

acc = metrics.get("final_accuracy") or metrics.get("accuracy") or metrics.get("avg_accuracy")
f1 = metrics.get("token_f1_mean") or metrics.get("final_token_f1") or metrics.get("token_f1")
seen = metrics.get("seen_accuracy") or metrics.get("final_seen_accuracy")
unseen = metrics.get("unseen_accuracy") or metrics.get("final_unseen_accuracy")

parts = [f"run `{run_name}` 已完成"]
if phase:
    parts[0] = f"Phase {phase} {parts[0]}"
if acc is not None:
    parts.append(f"accuracy={acc}")
if f1 is not None:
    parts.append(f"token_f1={f1}")
if seen is not None:
    parts.append(f"seen_acc={seen}")
if unseen is not None:
    parts.append(f"unseen_acc={unseen}")
if not metrics:
    parts.append("（未找到 final_metrics.json）")

summary = "，".join(parts) + "。"
Path(log_file).write_text(summary + "\n", encoding="utf-8")
print(summary)
PY

SUMMARY="$(cat "$LOG_FILE")"
REASON="milestone"
if [[ "$PHASE" == "1" ]]; then
  REASON="milestone"
  MESSAGE="【Phase 1 优先任务完成】${SUMMARY} 请用中文向用户汇报 v8_sota_5 instrdialog++ seed=123 最终指标，并确认 Phase 2 baseline 队列已自动接续。"
else
  MESSAGE="${SUMMARY}"
fi

if [[ -x "$WAKE_SCRIPT" ]] || [[ -f "$WAKE_SCRIPT" ]]; then
  bash "$WAKE_SCRIPT" --reason "$REASON" --message "$MESSAGE"
fi

python3 experiments/v8_sota5_campaign/supervisor/status_report.py 2>/dev/null || true

echo "[on_run_complete] done run=$RUN_NAME phase=${PHASE:-?}" | tee -a "$LOG_FILE"
