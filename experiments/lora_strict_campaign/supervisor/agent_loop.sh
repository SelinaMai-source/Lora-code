#!/usr/bin/env bash
# Cursor agent wake loop for lora_run_v10 strict alignment campaign.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

SUPERVISOR_DIR="experiments/lora_strict_campaign/supervisor"
POLL_SEC="${STRICT_AGENT_POLL_SEC:-60}"
REPORT_SEC="${STRICT_AGENT_REPORT_SEC:-1800}"
FLAG="${SUPERVISOR_DIR}/STRICT_AGENT_WAKE.flag"
STATE_JSON="${SUPERVISOR_DIR}/STRICT_MONITOR_STATE.json"
WAKE_LOG="${SUPERVISOR_DIR}/agent_wake.log"
WAKE_SCRIPT="${SUPERVISOR_DIR}/cursor_agent_wake.sh"

emit_from_flag() {
  python3 - "$FLAG" <<'PY'
import json, sys
from pathlib import Path
flag = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
flag.setdefault("kind", "wake")
print("AGENT_LOOP_WAKE_STRICT " + json.dumps(flag, ensure_ascii=False))
PY
}

emit_periodic_report() {
  local summary
  summary=$(python3 - "$STATE_JSON" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    print("strict 监控运行中，状态文件尚未生成。")
    raise SystemExit(0)
st = json.loads(p.read_text(encoding="utf-8"))
sa = st.get("strict_alignment") or {}
citb = st.get("citb") or {}
print(
    f"strict_cells={sa.get('strict_cells', 0)}; "
    f"CITB={citb.get('phase', '?')}; "
    f"GPU_train={st.get('gpu_train_count', 0)}"
)
PY
)
  bash "$WAKE_SCRIPT" --reason report --message "定期汇报：${summary}"
}

mkdir -p "$SUPERVISOR_DIR"
echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] strict agent_loop started poll=${POLL_SEC}s report=${REPORT_SEC}s" \
  | tee -a "${WAKE_LOG}"

last_report=$(date +%s)
last_flag_mtime=0

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
      echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_STRICT (flag)" >> "${WAKE_LOG}"
      rm -f "${FLAG}"
      last_flag_mtime=$flag_mtime
    fi
  elif [[ -n "${pending}" ]]; then
    bash "$WAKE_SCRIPT" --reason issue --message "${pending}"
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_STRICT (pending_agent)" >> "${WAKE_LOG}"
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
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] emitted AGENT_LOOP_WAKE_STRICT (periodic)" >> "${WAKE_LOG}"
    last_report=$now
  fi

  sleep "${POLL_SEC}"
done
