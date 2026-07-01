#!/usr/bin/env python3
"""Generate STRICT_STATUS.md and refresh strict alignment summary."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[3]
SUPERVISOR_DIR = REPO / "experiments/lora_strict_campaign/supervisor"
STATUS_PATH = SUPERVISOR_DIR / "STRICT_STATUS.md"
STATE_PATH = SUPERVISOR_DIR / "STRICT_MONITOR_STATE.json"
SUMMARY_PATH = REPO / "results/tables/lora_run_v10_strict_alignment_summary.json"
CITB_STATE = REPO / "results/logs/citb/post_citb_supervisor_state.json"
CITB_CMP = REPO / "results/tables/citb_instrdialog_paper_comparison.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _tmux_sessions() -> List[str]:
    try:
        out = subprocess.check_output(["tmux", "list-sessions", "-F", "#{session_name}"], text=True)
        return [s.strip() for s in out.splitlines() if s.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _refresh_strict_summary() -> Dict[str, Any]:
    script = REPO / "scripts/check_lora_run_v10_strict_alignment.py"
    if script.is_file():
        subprocess.run(["python3", str(script)], cwd=str(REPO), check=False)
    return _load_json(SUMMARY_PATH)


def _citb_train_procs() -> List[str]:
    try:
        out = subprocess.check_output(
            ["pgrep", "-af", "run_continual_instruct_tuning.py"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [ln.strip() for ln in out.splitlines() if "pgrep" not in ln]


def write_report() -> Dict[str, Any]:
    SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
    summary = _refresh_strict_summary()
    sa = summary.get("summary", {})
    strict_cells = len(summary.get("strict_cells") or [])
    near = len(summary.get("near_strict_cells") or [])
    blocked = len(summary.get("blocked_cells") or [])

    citb_state = _load_json(CITB_STATE)
    citb_cmp = _load_json(CITB_CMP)
    ft_ar = replay_ar = None
    if citb_cmp.get("methods"):
        ft = citb_cmp["methods"].get("FT_INSTR", {}).get("local", {})
        rp = citb_cmp["methods"].get("REPLAY", {}).get("local", {})
        ft_ar = ft.get("average_accuracy")
        replay_ar = rp.get("average_accuracy")

    sessions = _tmux_sessions()
    citb_tmux = [s for s in sessions if "citb" in s or "ct0" in s or "lfpt5" in s]
    trains = _citb_train_procs()

    lines = [
        "# lora_run_v10 Strict Alignment — 状态",
        "",
        f"Updated: {_now()}",
        "",
        "## Strict 矩阵",
        "",
        f"- **strict_cells**: {strict_cells}",
        f"- **near_strict**: {near}",
        f"- **blocked / needs audit**: {blocked}",
        "",
        "## CITB InstrDialog（Sequential / Replay LoRA）",
        "",
        f"- supervisor phase: `{citb_state.get('phase', '—')}`",
        f"- detail: {citb_state.get('detail', '—')}",
        f"- FT_INSTR AR (local): {ft_ar if ft_ar is not None else '—'}",
        f"- Replay AR (local): {replay_ar if replay_ar is not None else '—'}",
        f"- paper targets: FT 35.7 / Replay 40.4 (rougeL AR)",
        "",
        "## 运行中",
        "",
        f"- CITB/GPU 进程数: {len(trains)}",
        f"- 相关 tmux: {', '.join(citb_tmux) if citb_tmux else '—'}",
        "",
        "## 长期目标",
        "",
        "1. CITB paper 数值对齐（Stage-1 → Stage-2 → collect → 对比 → rerun）",
        "2. 其余 baseline gap-repair（GPU 空闲时 CPU 并行）",
        "3. LFPT5 clean rerun 排队",
        "",
    ]
    STATUS_PATH.write_text("\n".join(lines), encoding="utf-8")

    state = _load_json(STATE_PATH)
    state.update(
        {
            "last_status_report": _now(),
            "strict_alignment": {
                "strict_cells": strict_cells,
                "near_strict": near,
                "blocked": blocked,
            },
            "citb": {
                "phase": citb_state.get("phase"),
                "detail": citb_state.get("detail"),
                "ft_ar": ft_ar,
                "replay_ar": replay_ar,
            },
            "gpu_train_count": len(trains),
            "citb_tmux": citb_tmux,
        }
    )
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state


def main() -> None:
    write_report()
    print(f"Wrote {STATUS_PATH}")


if __name__ == "__main__":
    main()
