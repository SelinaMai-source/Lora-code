#!/usr/bin/env bash
# Write STRICT_AGENT_WAKE.flag and optionally emit AGENT_LOOP_WAKE_STRICT for Cursor /loop.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SUPERVISOR_DIR="${ROOT}/experiments/lora_strict_campaign/supervisor"
FLAG="${SUPERVISOR_DIR}/STRICT_AGENT_WAKE.flag"
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
      echo "Usage: cursor_agent_wake.sh --reason issue|report|milestone --message \"...\""
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$REASON" ]] || { echo "Missing --reason" >&2; exit 1; }

case "$REASON" in
  issue) KIND="wake" ;;
  report|milestone) KIND="report" ;;
  *) echo "Invalid --reason: $REASON" >&2; exit 1 ;;
esac

BASE_PROMPT="请阅读 ${PROMPT_FILE}、STRICT_STATUS.md、STRICT_MONITOR_STATE.json。工作目录：${ROOT}。"

if [[ "$KIND" == "wake" ]]; then
  PROMPT="${BASE_PROMPT} pending_action=fix：按 AGENT_LOOP_PROMPT 修理 strict 缺口、重启 tmux、推进 CITB paper 对齐；完成后清除 pending_agent。"
else
  PROMPT="${BASE_PROMPT} 用中文向用户汇报 strict 对齐进度、CITB paper 对比、GPU 任务与 blocker。"
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
    "wake_reason": "STRICT_AGENT_WAKE.flag",
}
Path(flag_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
if not write_only:
    print("AGENT_LOOP_WAKE_STRICT " + json.dumps(payload, ensure_ascii=False))
PY

echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] cursor_agent_wake reason=${REASON} kind=${KIND}" >> "$WAKE_LOG"
