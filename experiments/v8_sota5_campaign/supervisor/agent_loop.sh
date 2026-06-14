#!/bin/bash
# Cursor agent wake loop for v8_sota5 campaign (see /root/.cursor/skills-cursor/loop/SKILL.md).
#
# Launch:
#   tmux new-session -d -s v8s5camp_agent_loop \
#     'bash experiments/v8_sota5_campaign/supervisor/agent_loop.sh'
#
# Wake format (stdout sentinel for /loop):
#   AGENT_LOOP_WAKE_CAMPAIGN {"prompt":"...","kind":"wake|report|tick",...}
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SUPERVISOR_DIR="experiments/v8_sota5_campaign/supervisor"
POLL_SEC="${CAMPAIGN_AGENT_POLL_SEC:-30}"
REPORT_SEC="${CAMPAIGN_AGENT_REPORT_SEC:-1800}"
FLAG="${SUPERVISOR_DIR}/CAMPAIGN_AGENT_WAKE.flag"
STATE_JSON="${SUPERVISOR_DIR}/CAMPAIGN_MONITOR_STATE.json"
WAKE_LOG="${SUPERVISOR_DIR}/agent_wake.log"
WAKE_SCRIPT="${SUPERVISOR_DIR}/cursor_agent_wake.sh"

emit_from_flag() {
  python3 - "$FLAG" <<'PY'
import json, sys
from pathlib import Path
flag = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
flag.setdefault("kind", "wake")
print("AGENT_LOOP_WAKE_CAMPAIGN " + json.dumps(flag, ensure_ascii=False))
PY
}

emit_periodic_report() {
  local summary
  summary=$(python3 - "$STATE_JSON" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    print("战役监控运行中，状态文件尚未生成。")
    sys.exit(0)
st = json.loads(p.read_text(encoding="utf-8"))
m = st.get("manifest") or {}
run = st.get("current_run") or "无"
seg = (st.get("current_segment") or {}).get("label", "—")
total = m.get("total", 47)
print(f"进度 {m.get('completed', '?')}/{total}，当前 run={run}，segment={seg}")
PY
)
  bash "$WAKE_SCRIPT" --reason report --message "定期汇报：${summary}"
}

mkdir -p "$SUPERVISOR_DIR"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] agent_loop started poll=${POLL_SEC}s report=${REPORT_SEC}s" \
  | tee -a "${WAKE_LOG}"

last_report=$(date +%s)
last_flag_mtime=0

# Per loop skill: first sentinel after initial sleep (no double-run on startup).
sleep "${POLL_SEC}"

while true; do
  now=$(date +%s)

  pending=""
  if [[ -f "${STATE_JSON}" ]]; then
    pending=$(python3 - "$STATE_JSON" <<'PY'
import json, sys
from pathlib import Path
st = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(st.get("pending_agent") or "")
PY
)
  fi

  if [[ -f "${FLAG}" ]]; then
    flag_mtime=$(stat -c %Y "${FLAG}" 2>/dev/null || echo 0)
    if (( flag_mtime > last_flag_mtime )); then
      emit_from_flag
      echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_CAMPAIGN (flag)" >> "${WAKE_LOG}"
      rm -f "${FLAG}"
      last_flag_mtime=$flag_mtime
    fi
  elif [[ -n "${pending}" ]]; then
    bash "$WAKE_SCRIPT" --reason issue --message "${pending}"
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_CAMPAIGN (pending_agent)" >> "${WAKE_LOG}"
    python3 - "$STATE_JSON" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
st = json.loads(p.read_text(encoding="utf-8"))
st["pending_agent"] = None
st["pending_action"] = None
p.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
PY
  fi

  if (( now - last_report >= REPORT_SEC )); then
    emit_periodic_report
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_CAMPAIGN (periodic report)" >> "${WAKE_LOG}"
    last_report=$now
  fi

  sleep "${POLL_SEC}"
done
