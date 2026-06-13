#!/usr/bin/env bash
# 暂停 v8s5camp_serial（仅杀 train.py + manifest runner），保存 PRIORITY_QUEUE.state。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PRIORITY_STATE="experiments/v8_sota5_campaign/PRIORITY_QUEUE.state"
PRIORITY_CONFIG="${PRIORITY_CONFIG:-configs/paper/v8_sota5_campaign/ours_multiseed/instrdialogpp__v8_sota_5__s123.yaml}"

python3 - "$PRIORITY_STATE" "$PRIORITY_CONFIG" "$ROOT" <<'PY'
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

state_path, priority_config, repo = sys.argv[1:4]
repo = Path(repo)

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

# Current train.py
paused_run = None
paused_segment = 0
train_pid = None
try:
    out = subprocess.check_output(["pgrep", "-af", "core/train.py"], text=True)
except subprocess.CalledProcessError:
    out = ""
for line in out.splitlines():
    if "train.py" not in line:
        continue
    m = re.search(r"^(\d+)\s+(.*)$", line.strip())
    if not m:
        continue
    pid, cmd = int(m.group(1)), m.group(2)
    cfg_m = re.search(r"--config\s+(\S+)", cmd)
    if cfg_m:
        try:
            import yaml
            data = yaml.safe_load(Path(cfg_m.group(1)).read_text(encoding="utf-8")) or {}
            paused_run = (data.get("output") or {}).get("run_name")
        except Exception:
            pass
    train_pid = pid
    break

if paused_run:
    run_dir = repo / "results/runs" / paused_run
    segs = sorted(run_dir.glob("segment_*")) if run_dir.is_dir() else []
    paused_segment = len(segs)

import yaml
pj_cfg = yaml.safe_load((repo / priority_config).read_text(encoding="utf-8")) or {}
priority_run = (pj_cfg.get("output") or {}).get("run_name", "")

manifest_pid = None
try:
    out = subprocess.check_output(["pgrep", "-af", "run_from_manifest"], text=True)
    for line in out.splitlines():
        if "run_from_manifest.py" in line and "v8_sota5_campaign" in line:
            manifest_pid = int(line.strip().split()[0])
            break
except subprocess.CalledProcessError:
    pass

serial_pids = []
try:
    out = subprocess.check_output(["pgrep", "-af", "run_campaign_serial"], text=True)
    for line in out.splitlines():
        if "run_campaign_serial.sh" in line:
            serial_pids.append(int(line.strip().split()[0]))
except subprocess.CalledProcessError:
    pass

state = {
    "status": "priority_running",
    "created_at": now(),
    "paused_run": paused_run,
    "paused_segment": paused_segment,
    "paused_category": "baseline_multiseed",
    "paused_note": "无 final_metrics，恢复串行时将从头重跑该 run",
    "train_pid": train_pid,
    "manifest_pid": manifest_pid,
    "priority_job": {
        "run_name": priority_run,
        "config_path": priority_config,
        "benchmark": "instrdialog++",
        "seed": 123,
        "variant": "v8_sota_5",
    },
}
Path(state_path).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[pause] wrote {state_path}")
print(json.dumps(state, indent=2, ensure_ascii=False))
PY

# Graceful stop: SIGTERM train + manifest runner only (never kill tmux / serial shell)
for pid in ${train_pid:-} ${manifest_pid:-}; do
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "[pause] SIGTERM pid=$pid"
    kill -TERM "$pid" 2>/dev/null || true
  fi
done

sleep 3
for pat in "core/train.py" "run_from_manifest.py"; do
  pids=$(pgrep -f "$pat" 2>/dev/null || true)
  for pid in $pids; do
    cmd=$(ps -p "$pid" -o args= 2>/dev/null || true)
    if [[ "$cmd" == *"v8_sota5_campaign"* || "$cmd" == *"core/train.py"* ]]; then
      echo "[pause] SIGKILL pid=$pid (still alive)"
      kill -KILL "$pid" 2>/dev/null || true
    fi
  done
done

echo "[pause] serial paused; supervisor/agent_loop/tmux untouched"
