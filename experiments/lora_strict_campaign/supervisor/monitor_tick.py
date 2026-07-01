#!/usr/bin/env python3
"""Strict alignment health tick: CITB pipeline, tmux guardians, gap-repair, agent wake."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[3]
SUPERVISOR_DIR = REPO / "experiments/lora_strict_campaign/supervisor"
LOG_PATH = SUPERVISOR_DIR / "STRICT_MONITOR.log"
STATE_PATH = SUPERVISOR_DIR / "STRICT_MONITOR_STATE.json"
WAKE_SCRIPT = SUPERVISOR_DIR / "cursor_agent_wake.sh"
STATUS_SCRIPT = SUPERVISOR_DIR / "status_report.py"

GUARDIAN_TMUX = [
    ("citb_replay_monitor", "results/logs/citb/monitor_replay_and_ct0.sh"),
    ("ct0_download", "results/logs/gap_repair/start_proxy_and_download_ct0.sh"),
]

FAIL_PATTERNS = ["Traceback (most recent call last)", "CUDA out of memory", "OutOfMemoryError"]
CITB_LOG_GLOB = [
    "results/logs/citb/stage2_ft_instr_seed515_rerun.log",
    "results/logs/citb/stage2_replay50_seed515_rerun.log",
    "results/logs/citb/stage2_ft_instr_seed227_rerun.log",
    "results/logs/citb/stage2_replay50_seed227_rerun.log",
]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _log(msg: str) -> None:
    SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{_now()}] {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _default_state() -> Dict[str, Any]:
    return {
        "last_tick": None,
        "strict_alignment": {"strict_cells": 0, "near_strict": 0, "blocked": 40},
        "citb": {},
        "gpu_train_count": 0,
        "issues": [],
        "auto_fixes": [],
        "pending_agent": None,
        "pending_action": None,
    }


def _load_state() -> Dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            st = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            base = _default_state()
            for k, v in base.items():
                st.setdefault(k, v)
            return st
        except json.JSONDecodeError:
            pass
    return _default_state()


def _save_state(state: Dict[str, Any]) -> None:
    state["last_tick"] = _now()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _invoke_wake(*, reason: str, message: str) -> None:
    if not WAKE_SCRIPT.is_file():
        return
    subprocess.run(
        ["bash", str(WAKE_SCRIPT), "--reason", reason, "--message", message, "--write-only"],
        cwd=str(REPO),
        check=False,
    )


def _tmux_sessions() -> List[str]:
    try:
        out = subprocess.check_output(["tmux", "list-sessions", "-F", "#{session_name}"], text=True)
        return [s.strip() for s in out.splitlines() if s.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def _launch_tmux(session: str, rel_cmd: str) -> None:
    if session in _tmux_sessions():
        return
    cmd = f"cd {REPO} && bash {rel_cmd}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, cmd], check=False)
    _log(f"AUTO_FIX launched tmux {session}")


def _citb_trains() -> List[str]:
    try:
        out = subprocess.check_output(["pgrep", "-af", "run_continual_instruct_tuning.py"], text=True)
    except subprocess.CalledProcessError:
        return []
    return [ln for ln in out.splitlines() if "pgrep" not in ln]


def _tail_has_failure(path: Path, n: int = 400) -> Optional[str]:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    tail = "\n".join(text.splitlines()[-n:])
    for pat in FAIL_PATTERNS:
        if pat in tail:
            return pat
    return None


def _strict_cells_closed(prev: Dict[str, Any], cur: Dict[str, Any]) -> bool:
    p = int((prev.get("strict_alignment") or {}).get("strict_cells", 0))
    c = int((cur.get("strict_alignment") or {}).get("strict_cells", 0))
    return c > p


def main() -> int:
    prev = _load_state()
    if STATUS_SCRIPT.is_file():
        subprocess.run(["python3", str(STATUS_SCRIPT)], cwd=str(REPO), check=False)
    state = _load_state()

    issues: List[str] = []
    fixes: List[str] = []
    sessions = _tmux_sessions()
    trains = _citb_trains()
    state["gpu_train_count"] = len(trains)

    for session, script in GUARDIAN_TMUX:
        if session not in sessions:
            _launch_tmux(session, script)
            fixes.append(f"restarted {session}")

    for rel in CITB_LOG_GLOB:
        fail = _tail_has_failure(REPO / rel)
        if fail:
            issues.append(f"{rel}: {fail}")
            state["pending_agent"] = f"CITB log failure in {rel}: {fail}"
            state["pending_action"] = "fix"
            _invoke_wake(reason="issue", message=state["pending_agent"])

    sa = state.get("strict_alignment") or {}
    if int(sa.get("strict_cells", 0)) == 0:
        citb = state.get("citb") or {}
        phase = str(citb.get("phase", ""))
        if "running" not in phase and len(trains) == 0:
            queue_scripts = [
                "results/logs/citb/run_stage2_paper_seed515_rerun_queue.sh",
                "results/logs/citb/run_stage2_paper_seed227_rerun_queue.sh",
            ]
            for script in queue_scripts:
                if (REPO / script).is_file() and "citb_stage2" not in " ".join(sessions):
                    issues.append("GPU idle with no CITB queue tmux")
                    state["pending_agent"] = "GPU idle: verify CITB queue / post_citb_supervisor"
                    state["pending_action"] = "fix"
                    break

    if _strict_cells_closed(prev, state):
        _invoke_wake(
            reason="milestone",
            message=f"strict_cells increased to {sa.get('strict_cells')}",
        )

    state["issues"] = issues[-10:]
    state["auto_fixes"] = fixes[-10:]
    _save_state(state)

    if issues:
        _log(f"issues={issues} fixes={fixes}")
    else:
        _log(f"ok strict_cells={sa.get('strict_cells', 0)} gpu_trains={len(trains)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
