#!/bin/bash
# Write CAMPAIGN_AGENT_WAKE.flag and emit AGENT_LOOP_WAKE_CAMPAIGN for Cursor /loop.
#
# Usage:
#   bash cursor_agent_wake.sh --reason issue|report|milestone --message "..."
#   bash cursor_agent_wake.sh --reason report --message "test" --write-only   # flag only, no stdout
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUPERVISOR_DIR="${ROOT}/experiments/v8_sota5_campaign/supervisor"
FLAG="${SUPERVISOR_DIR}/CAMPAIGN_AGENT_WAKE.flag"
WAKE_LOG="${SUPERVISOR_DIR}/agent_wake.log"
PROMPT_FILE="${SUPERVISOR_DIR}/AGENT_LOOP_PROMPT.md"

REASON=""
MESSAGE=""
WRITE_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reason) REASON="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --write-only) WRITE_ONLY=1; shift ;;
    -h|--help)
      cat <<EOF
Usage: cursor_agent_wake.sh --reason issue|report|milestone --message "..."

  issue      → kind=wake, agent should diagnose and fix
  report     → kind=report, agent should summarize status to user
  milestone  → kind=report, run completed or priority queue milestone
EOF
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$REASON" ]]; then
  echo "Missing --reason (issue|report|milestone)" >&2
  exit 1
fi

case "$REASON" in
  issue) KIND="wake" ;;
  report|milestone) KIND="report" ;;
  *)
    echo "Invalid --reason: $REASON (use issue|report|milestone)" >&2
    exit 1
    ;;
esac

BASE_PROMPT="请阅读 ${PROMPT_FILE}、CAMPAIGN_STATUS.md、CAMPAIGN_MONITOR_STATE.json 和 CAMPAIGN_MONITOR.log。工作目录：${ROOT}。"

if [[ "$KIND" == "wake" ]]; then
  PROMPT="${BASE_PROMPT} pending_action=fix：诊断故障、修复代码/脚本、必要时重启 tmux 串行训练；完成后清除 pending_agent。禁止在同一 GPU 上并行多个 train.py。勿杀掉健康的 train.py。"
else
  PROMPT="${BASE_PROMPT} 用中文向用户汇报 v8_sota5 战役进度、当前 run、segment 进度、错误与 ETA；引用 CAMPAIGN_STATUS.md 中的关键指标。"
fi

[[ -n "$MESSAGE" ]] && PROMPT="${PROMPT} 附言：${MESSAGE}"

mkdir -p "$SUPERVISOR_DIR"

python3 - "$FLAG" "$REASON" "$MESSAGE" "$KIND" "$PROMPT" "$ROOT" "$WRITE_ONLY" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

flag_path, reason, message, kind, prompt, repo, write_only = sys.argv[1:8]
write_only = write_only == "1"
payload = {
    "reason": reason,
    "message": message,
    "kind": kind,
    "prompt": prompt,
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    "repo": repo,
    "wake_reason": "CAMPAIGN_AGENT_WAKE.flag",
}
Path(flag_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
if not write_only:
    print("AGENT_LOOP_WAKE_CAMPAIGN " + json.dumps(payload, ensure_ascii=False))
PY

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] cursor_agent_wake reason=${REASON} kind=${KIND} write_only=${WRITE_ONLY}" >> "$WAKE_LOG"
