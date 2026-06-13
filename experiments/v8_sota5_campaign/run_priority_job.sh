#!/usr/bin/env bash
# 单 GPU 优先任务：ours instrdialog++ seed 123 (v8_sota_5)
# 完成后写 CAMPAIGN_AGENT_WAKE.flag、汇报 metrics、恢复串行队列。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source experiments/v8_sota5_campaign/campaign.env

SUPERVISOR_DIR="experiments/v8_sota5_campaign/supervisor"
PRIORITY_STATE="experiments/v8_sota5_campaign/PRIORITY_QUEUE.state"
CONFIG="${PRIORITY_CONFIG:-configs/paper/v8_sota5_campaign/ours_multiseed/instrdialogpp__v8_sota_5__s123.yaml}"
LOG_DIR="$ROOT/results/logs/v8_sota5_campaign"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/priority_$(date +%Y%m%d_%H%M%S).log"

RUN_NAME="$(python3 - "$CONFIG" <<'PY'
import yaml, sys
from pathlib import Path
cfg = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
print((cfg.get("output") or {}).get("run_name", ""))
PY
)"

echo "[priority] config=$CONFIG run_name=$RUN_NAME" | tee -a "$LOG_FILE"
echo "[priority] WANDB_PROJECT=$WANDB_PROJECT WANDB_MODE=$WANDB_MODE" | tee -a "$LOG_FILE"
if [[ "${WANDB_MODE:-online}" == "disabled" ]]; then
  echo "[priority] ERROR: WANDB_MODE=disabled — campaign requires online W&B logging" | tee -a "$LOG_FILE"
  exit 1
fi
echo "[priority] log=$LOG_FILE" | tee -a "$LOG_FILE"

FINAL_METRICS="$ROOT/results/runs/$RUN_NAME/final_metrics.json"
if [[ -f "$FINAL_METRICS" ]]; then
  echo "[priority] skip — final_metrics.json already exists" | tee -a "$LOG_FILE"
else
  echo "[priority] starting train.py" | tee -a "$LOG_FILE"
  python3 core/train.py --config "$CONFIG" 2>&1 | tee -a "$LOG_FILE"
fi

# --- completion: metrics summary + agent wake + resume serial ---
python3 - "$RUN_NAME" "$PRIORITY_STATE" "$SUPERVISOR_DIR" "$ROOT" <<'PY' | tee -a "$LOG_FILE"
import json, subprocess, sys
from pathlib import Path

run_name, state_path, supervisor_dir, repo = sys.argv[1:5]
repo = Path(repo)
final_p = repo / "results/runs" / run_name / "final_metrics.json"
metrics = {}
if final_p.is_file():
    try:
        metrics = json.loads(final_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        pass

acc = metrics.get("final_accuracy") or metrics.get("accuracy") or metrics.get("avg_accuracy")
f1 = metrics.get("token_f1_mean") or metrics.get("final_token_f1")
summary = f"优先任务 {run_name} 已完成。"
if acc is not None:
    summary += f" accuracy={acc}"
if f1 is not None:
    summary += f" token_f1={f1}"
if not metrics:
    summary += " （未找到 final_metrics.json）"

state_p = Path(state_path)
state = {}
if state_p.is_file():
    try:
        state = json.loads(state_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        pass
state["status"] = "completed"
state["completed_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
state["final_metrics"] = metrics
state_p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[priority] updated {state_p}")

detail = f"请用中文向用户汇报优先 run `{run_name}` 的最终指标。{summary}"
wake_sh = repo / supervisor_dir / "cursor_agent_wake.sh"
if wake_sh.is_file():
    subprocess.run(
        ["bash", str(wake_sh), "--kind", "report", "--reason", "priority_completed",
         "--detail", detail, "--priority", "high",
         "--prompt", f"【优先任务完成】{detail} 请阅读 CAMPAIGN_STATUS.md 与 results/runs/{run_name}/final_metrics.json。"],
        cwd=str(repo), check=False,
    )

status_py = repo / supervisor_dir / "status_report.py"
if status_py.is_file():
    subprocess.run(
        ["python3", str(status_py), "--notify-agent", "--kind", "report",
         "--reason", "priority_completed", "--detail", detail, "--priority", "high"],
        cwd=str(repo), check=False,
    )
PY

echo "[priority] resuming serial queue from PRIORITY_QUEUE.state" | tee -a "$LOG_FILE"
bash experiments/v8_sota5_campaign/resume_serial_from_priority.sh 2>&1 | tee -a "$LOG_FILE"

echo "[priority] done" | tee -a "$LOG_FILE"
