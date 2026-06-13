#!/usr/bin/env python3
"""Generate CAMPAIGN_STATUS.md and update CAMPAIGN_MONITOR_STATE.json."""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[3]
CAMPAIGN_DIR = REPO / "experiments/v8_sota5_campaign"
SUPERVISOR_DIR = CAMPAIGN_DIR / "supervisor"
MANIFEST_PATH = CAMPAIGN_DIR / "manifest.csv"
STATUS_PATH = SUPERVISOR_DIR / "CAMPAIGN_STATUS.md"
STATE_JSON_PATH = SUPERVISOR_DIR / "CAMPAIGN_MONITOR_STATE.json"
RUNS_DIR = REPO / "results/runs"
LOG_DIR = REPO / "results/logs/v8_sota5_campaign"

OOM_PATTERNS = ["CUDA out of memory", "OutOfMemoryError", "out of memory"]
CRASH_PATTERNS = ["Traceback (most recent call last)", "Segmentation fault", "Killed"]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _load_state() -> Dict[str, Any]:
    if STATE_JSON_PATH.is_file():
        try:
            return json.loads(STATE_JSON_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _read_manifest() -> List[Dict[str, str]]:
    if not MANIFEST_PATH.is_file():
        return []
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _run_dir(run_name: str) -> Path:
    return RUNS_DIR / run_name


def _read_metrics_jsonl(run_dir: Path) -> Optional[Dict[str, Any]]:
    path = run_dir / "metrics.jsonl"
    if not path.is_file():
        return None
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def _segment_from_run(run_name: Optional[str]) -> Tuple[int, int, str]:
    if not run_name:
        return 0, 0, "—"
    run_dir = _run_dir(run_name)
    if not run_dir.is_dir():
        return 0, 0, "—"

    latest = _read_metrics_jsonl(run_dir)
    if latest is not None:
        seg_id = int(latest.get("segment_id", latest.get("segment", 0)) or 0)
        total = int(latest.get("total_segments", latest.get("num_segments", 0)) or 0)
        if total <= 0:
            cfg = run_dir / "config_snapshot.yaml"
            if cfg.is_file():
                try:
                    import yaml

                    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
                    stream_tasks = data.get("data", {}).get("processed_stream_limit_tasks", -1)
                    if stream_tasks and int(stream_tasks) > 0:
                        total = int(stream_tasks)
                except Exception:
                    pass
        if total <= seg_id:
            segments = sorted(run_dir.glob("segment_*"))
            if segments:
                m = re.search(r"segment_(\d+)", segments[-1].name)
                if m:
                    total = max(total, int(m.group(1)) + 1)
                total = max(total, len(segments))
        label = f"{seg_id + 1}/{total}" if total else str(seg_id + 1)
        return seg_id + 1, total, label

    segments = sorted(run_dir.glob("segment_*"))
    n = len(segments)
    total = n
    cfg = run_dir / "config_snapshot.yaml"
    if cfg.is_file():
        try:
            import yaml

            data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            stream_tasks = data.get("data", {}).get("processed_stream_limit_tasks", -1)
            if stream_tasks and int(stream_tasks) > 0:
                total = int(stream_tasks)
        except Exception:
            pass
    if total <= n and segments:
        m = re.search(r"segment_(\d+)", segments[-1].name)
        if m:
            total = max(total, int(m.group(1)) + 1)
    label = f"{n}/{total}" if total else str(n)
    return n, total, label


def _parse_run_from_train(cmd: str) -> Optional[str]:
    m = re.search(r"--config\s+(\S+)", cmd)
    if not m:
        return None
    cfg_path = Path(m.group(1))
    if not cfg_path.is_absolute():
        cfg_path = REPO / cfg_path
    try:
        import yaml

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        output = data.get("output") or {}
        run_name = str(output.get("run_name", "")).strip()
        return run_name or None
    except Exception:
        return None


def _active_train_run() -> Tuple[Optional[str], Optional[str]]:
    try:
        out = subprocess.check_output(["pgrep", "-af", "core/train.py"], text=True)
    except subprocess.CalledProcessError:
        return None, None
    for line in out.splitlines():
        if "train.py" not in line:
            continue
        m = re.match(r"^(\d+)\s+(.*)$", line.strip())
        if not m:
            continue
        cmd = m.group(2)
        if "v8s5camp" in cmd or "v8_sota5_campaign" in cmd:
            return _parse_run_from_train(cmd), cmd
        cfg_m = re.search(r"--config\s+(\S+)", cmd)
        if cfg_m and "v8_sota5_campaign" in cfg_m.group(1):
            return _parse_run_from_train(cmd), cmd
    return None, None


def _manifest_stats(rows: List[Dict[str, str]], active_run: Optional[str]) -> Dict[str, Any]:
    completed: List[str] = []
    failed: List[str] = []
    queued: List[str] = []
    for row in rows:
        run_name = row["run_name"].strip()
        if not run_name.endswith("_v8s5camp") and "v8s5camp" not in run_name:
            continue
        final_p = _run_dir(run_name) / "final_metrics.json"
        if final_p.is_file():
            completed.append(run_name)
        elif active_run and run_name == active_run:
            pass
        elif _run_dir(run_name).is_dir():
            failed.append(run_name)
        else:
            queued.append(run_name)

    total = len([r for r in rows if "v8s5camp" in r["run_name"]])
    if total == 0:
        total = len(rows)
    return {
        "total": total,
        "completed": len(completed),
        "failed": len(failed),
        "running": 1 if active_run else 0,
        "queued": len(queued),
        "completed_runs": completed,
        "failed_runs": failed,
    }


def _scan_log_errors() -> List[str]:
    errors: List[str] = []
    if not LOG_DIR.is_dir():
        return errors
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    for log in logs:
        try:
            tail = log.read_bytes()[-12000:].decode("utf-8", errors="replace")
        except OSError:
            continue
        for pat in OOM_PATTERNS:
            if pat.lower() in tail.lower():
                errors.append(f"OOM: {log.name}")
                break
        else:
            for pat in CRASH_PATTERNS:
                if pat in tail:
                    errors.append(f"崩溃: {log.name}")
                    break
    return errors


def _gpu_stats() -> Dict[str, Any]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.total,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
        parts = [x.strip() for x in out.strip().splitlines()[0].split(",")]
        if len(parts) >= 4:
            used, total, util = int(parts[1]), int(parts[2]), int(parts[3])
            return {
                "memory_used_mib": used,
                "memory_total_mib": total,
                "utilization_pct": util,
                "memory_pct": round(100.0 * used / max(total, 1), 1),
            }
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, IndexError):
        pass
    return {}


def _tmux_campaign_session() -> Optional[str]:
    names = [
        "v8s5camp_priority",
        "v8s5camp_serial",
        "v8s5camp_queue",
        "v8s5camp_baselines",
        "v8s5camp_ours",
        "v8s5camp_ablation",
    ]
    try:
        out = subprocess.check_output(["tmux", "list-sessions", "-F", "#{session_name}"], text=True)
        sessions = {s.strip() for s in out.splitlines()}
        for n in names:
            if n in sessions:
                return n
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def _priority_state() -> Optional[Dict[str, Any]]:
    p = CAMPAIGN_DIR / "PRIORITY_QUEUE.state"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _next_steps(
    manifest: Dict[str, Any],
    issues: List[str],
    active_run: Optional[str],
    priority: Optional[Dict[str, Any]],
) -> List[str]:
    steps: List[str] = []
    if issues:
        steps.append("Agent 需诊断 CAMPAIGN_MONITOR.log 中的错误并修复后重启串行训练。")
    elif manifest["completed"] >= manifest["total"]:
        steps.append("全部 manifest 已完成，汇总 final_metrics 并更新论文表格。")
    elif priority and priority.get("status") == "completed":
        steps.append("优先任务已完成，恢复 v8s5camp_serial 串行队列。")
    elif not active_run and manifest["completed"] < manifest["total"]:
        steps.append("无活跃 train.py：确认 v8s5camp_serial tmux 存活，必要时 bash tmux_run_campaign_serial.sh。")
    elif active_run:
        steps.append(f"继续监控 `{active_run}`，等待 final_metrics.json 出现后自动进入下一 run。")
    else:
        steps.append("维持单 GPU 串行，勿并行 baselines/ours/ablation tmux。")
    return steps


def _extract_final_metrics(run_name: str) -> Optional[Dict[str, Any]]:
    p = _run_dir(run_name) / "final_metrics.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def collect_state(existing: Dict[str, Any]) -> Dict[str, Any]:
    rows = _read_manifest()
    active_run, train_cmd = _active_train_run()
    manifest = _manifest_stats(rows, active_run)
    seg_done, seg_total, seg_label = _segment_from_run(active_run)
    log_errors = _scan_log_errors()
    gpu = _gpu_stats()
    tmux = _tmux_campaign_session()
    priority = _priority_state()

    issues = list(existing.get("issues") or [])
    for err in log_errors:
        if err not in issues:
            issues.append(err)

    state: Dict[str, Any] = {
        **existing,
        "last_status_report": _now(),
        "campaign_tmux": tmux,
        "campaign_tmux_alive": bool(tmux),
        "current_run": active_run,
        "running_run": active_run,
        "train_cmd": train_cmd,
        "current_segment": {
            "index": seg_done,
            "total": seg_total,
            "label": seg_label,
        },
        "manifest": {
            "total": manifest["total"],
            "completed": manifest["completed"],
            "failed": manifest["failed"],
            "running": manifest["running"],
            "queued": manifest["queued"],
        },
        "gpu": gpu or existing.get("gpu") or {},
        "log_errors": log_errors,
        "issues": issues,
        "next_steps": _next_steps(manifest, issues, active_run, priority),
    }
    return state


def build_report(state: Dict[str, Any]) -> str:
    manifest = state.get("manifest") or {}
    total = int(manifest.get("total", 47))
    completed = int(manifest.get("completed", 0))
    failed = int(manifest.get("failed", 0))
    queued = int(manifest.get("queued", 0))
    running_n = int(manifest.get("running", 0))

    current_run = state.get("current_run")
    seg = state.get("current_segment") or {}
    seg_label = seg.get("label", "—")
    gpu = state.get("gpu") or {}
    tmux = state.get("campaign_tmux") or "无"
    last_tick = state.get("last_tick") or state.get("last_status_report") or "—"
    issues = state.get("issues") or []
    log_errors = state.get("log_errors") or []
    auto_fixes = state.get("auto_fixes") or []
    pending = state.get("pending_agent")
    next_steps = state.get("next_steps") or []

    pct = round(100.0 * completed / max(total, 1), 1)
    lines = [
        "# v8_sota5 战役状态报告",
        "",
        f"> 自动生成于 {_now()}",
        "",
        "## 总览",
        "",
        f"- **完成进度**: **{completed}/{total}** ({pct}%)",
        f"- 进行中: {running_n} | 排队: {queued} | 失败/半成品: {failed}",
        f"- tmux: `{tmux}` | 上次 tick: {last_tick}",
        "",
        "## 当前 Run",
        "",
    ]

    if current_run:
        lines.extend([
            f"- **Run**: `{current_run}`",
            f"- **Segment 进度**: {seg_label}",
        ])
        if gpu:
            lines.append(
                f"- **GPU**: {gpu.get('memory_used_mib', '?')}/{gpu.get('memory_total_mib', '?')} MiB "
                f"({gpu.get('memory_pct', '?')}%), 利用率 {gpu.get('utilization_pct', '?')}%"
            )
    else:
        lines.append("- 当前无活跃 campaign 训练")

    priority = _priority_state()
    if priority:
        lines.extend(["", "## 优先级队列", ""])
        pj = priority.get("priority_job") or {}
        lines.append(f"- 优先任务: `{pj.get('run_name', '?')}`")
        if priority.get("paused_run"):
            lines.append(
                f"- 已暂停: `{priority['paused_run']}` (segment {priority.get('paused_segment', '?')})"
            )

    all_errors = list(dict.fromkeys(log_errors + issues))
    lines.extend(["", "## 错误", ""])
    if all_errors:
        for e in all_errors:
            lines.append(f"- {e}")
    else:
        lines.append("- 无近期错误")

    if auto_fixes:
        lines.extend(["", "## 自动修复", ""])
        for f in auto_fixes:
            lines.append(f"- {f}")

    lines.extend(["", "## 下一步", ""])
    for step in next_steps:
        lines.append(f"- {step}")

    if pending:
        lines.extend(["", "## Agent 待办", "", f"- `{pending}`"])

    completed_runs = []
    for row in _read_manifest():
        rn = row["run_name"].strip()
        if (_run_dir(rn) / "final_metrics.json").is_file():
            completed_runs.append(rn)
    if completed_runs:
        lines.extend(["", "## 最近完成", ""])
        for rn in completed_runs[-5:]:
            fm = _extract_final_metrics(rn)
            acc = None
            if fm:
                acc = fm.get("final_accuracy") or fm.get("accuracy") or fm.get("avg_accuracy")
            extra = f" — accuracy={acc}" if acc is not None else ""
            lines.append(f"- `{rn}`{extra}")

    lines.extend(["", "---", "*由 status_report.py 自动生成*"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write CAMPAIGN_STATUS.md and update state JSON.")
    parser.add_argument("--no-state", action="store_true", help="Skip writing CAMPAIGN_MONITOR_STATE.json")
    args = parser.parse_args()

    SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_state()
    state = collect_state(existing)
    report = build_report(state)

    STATUS_PATH.write_text(report, encoding="utf-8")
    print(f"[status_report] wrote {STATUS_PATH}")

    if not args.no_state:
        STATE_JSON_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[status_report] updated {STATE_JSON_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
