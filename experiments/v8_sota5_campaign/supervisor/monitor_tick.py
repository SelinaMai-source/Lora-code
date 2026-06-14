#!/usr/bin/env python3
"""v8_sota5 campaign health tick: tmux, GPU, manifest, auto-repair, agent wake flags."""
from __future__ import annotations

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
LOG_PATH = SUPERVISOR_DIR / "CAMPAIGN_MONITOR.log"
STATE_PATH = SUPERVISOR_DIR / "CAMPAIGN_MONITOR_STATE.json"
WAKE_FLAG = SUPERVISOR_DIR / "CAMPAIGN_AGENT_WAKE.flag"
WAKE_SCRIPT = SUPERVISOR_DIR / "cursor_agent_wake.sh"
STATUS_SCRIPT = SUPERVISOR_DIR / "status_report.py"

CAMPAIGN_TRAINING_SESSIONS = [
    "v8s5camp_priority",
    "v8s5camp_serial",
    "v8s5camp_queue",
    "v8s5camp_baselines",
    "v8s5camp_ours",
    "v8s5camp_ablation",
]
PREFERRED_SERIAL_SESSION = "v8s5camp_serial"
PARALLEL_SESSIONS = {"v8s5camp_baselines", "v8s5camp_ours", "v8s5camp_ablation"}
SERIAL_LAUNCH_SCRIPT = CAMPAIGN_DIR / "tmux_run_campaign.sh"
LOG_DIR = REPO / "results/logs/v8_sota5_campaign"
STUCK_SEGMENT_SEC = 3600

OOM_PATTERNS = [
    "CUDA out of memory",
    "OutOfMemoryError",
    "out of memory",
    "CUDA error: out of memory",
]
CRASH_PATTERNS = [
    "Traceback (most recent call last)",
    "CalledProcessError",
    "Segmentation fault",
    "Killed",
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
        "campaign_tmux": None,
        "campaign_tmux_alive": False,
        "train_count": 0,
        "campaign_train_count": 0,
        "manifest": {"total": 47, "completed": 0, "failed": 0, "running": 0, "queued": 0},
        "current_run": None,
        "gpu": {},
        "issues": [],
        "auto_fixes": [],
        "pending_agent": None,
        "pending_action": None,
        "last_oom": None,
        "notes": [],
    }


def _load_state() -> Dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            st = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            base = _default_state()
            for k, v in base.items():
                st.setdefault(k, v)
            if isinstance(st.get("manifest"), dict):
                for mk, mv in base["manifest"].items():
                    st["manifest"].setdefault(mk, mv)
            return st
        except json.JSONDecodeError:
            pass
    return _default_state()


def _save_state(state: Dict[str, Any]) -> None:
    SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
    state["last_tick"] = _now()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _invoke_wake(*, reason: str, message: str) -> None:
    """Write CAMPAIGN_AGENT_WAKE.flag via cursor_agent_wake.sh (--write-only for agent_loop)."""
    if not WAKE_SCRIPT.is_file():
        _log(f"BLOCKED wake: missing {WAKE_SCRIPT}")
        return
    subprocess.run(
        ["bash", str(WAKE_SCRIPT), "--reason", reason, "--message", message, "--write-only"],
        cwd=str(REPO),
        check=False,
    )
    _log(f"WAKE_FLAG reason={reason} message={message}")


def _completed_runs(rows: List[Dict[str, str]]) -> List[str]:
    done: List[str] = []
    for row in rows:
        run_name = row["run_name"].strip()
        if (REPO / "results/runs" / run_name / "final_metrics.json").is_file():
            done.append(run_name)
    return done


def _phase_complete(rows: List[Dict[str, str]], phase: str) -> bool:
    phase_rows = [r for r in rows if str(r.get("phase", "")).strip() == phase]
    if not phase_rows:
        return False
    return all(
        (REPO / "results/runs" / r["run_name"].strip() / "final_metrics.json").is_file()
        for r in phase_rows
    )


def _latest_completed_run(prev_done: List[str], cur_done: List[str]) -> Optional[str]:
    new_runs = [r for r in cur_done if r not in prev_done]
    return new_runs[-1] if new_runs else None


def _run_status_report() -> None:
    if STATUS_SCRIPT.is_file():
        subprocess.run(["python3", str(STATUS_SCRIPT)], cwd=str(REPO), check=False)


def _tmux_sessions() -> List[str]:
    try:
        out = subprocess.check_output(["tmux", "list-sessions", "-F", "#{session_name}"], text=True)
        return [s.strip() for s in out.splitlines() if s.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def _train_processes() -> List[Dict[str, Any]]:
    try:
        out = subprocess.check_output(["pgrep", "-af", "core/train.py"], text=True)
    except subprocess.CalledProcessError:
        return []
    procs: List[Dict[str, Any]] = []
    for line in out.splitlines():
        line = line.strip()
        if "train.py" not in line:
            continue
        m = re.match(r"^(\d+)\s+(.*)$", line)
        if not m:
            continue
        procs.append({"pid": int(m.group(1)), "cmd": m.group(2), "is_campaign": False})
    return procs


def _is_campaign_train(cmd: str) -> bool:
    if "v8s5camp" in cmd or "v8_sota5_campaign" in cmd:
        return True
    m = re.search(r"--config\s+(\S+)", cmd)
    if m:
        cfg = m.group(1)
        if "v8_sota5_campaign" in cfg:
            return True
        try:
            text = Path(cfg).read_text(encoding="utf-8", errors="replace")
            if "v8s5camp" in text or "v8_sota5_campaign" in text:
                return True
        except OSError:
            pass
    return False


def _refine_campaign_flags(procs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for p in procs:
        p["is_campaign"] = _is_campaign_train(p["cmd"])
    return procs


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


def _read_manifest() -> List[Dict[str, str]]:
    if not MANIFEST_PATH.is_file():
        return []
    with MANIFEST_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _run_dir_for_row(row: Dict[str, str]) -> Path:
    return REPO / "results/runs" / row["run_name"].strip()


def _manifest_progress(
    rows: List[Dict[str, str]], active_run: Optional[str]
) -> Tuple[Dict[str, int], List[Dict[str, str]]]:
    completed = failed = queued = 0
    failed_rows: List[Dict[str, str]] = []
    for row in rows:
        run_name = row["run_name"].strip()
        run_dir = _run_dir_for_row(row)
        if (run_dir / "final_metrics.json").is_file():
            completed += 1
        elif active_run and run_name == active_run:
            pass
        elif run_dir.is_dir():
            failed += 1
            failed_rows.append(row)
        else:
            queued += 1
    counts = {
        "total": len(rows),
        "completed": completed,
        "failed": failed,
        "running": 1 if active_run else 0,
        "queued": queued,
    }
    return counts, failed_rows


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
        return str((data.get("output") or {}).get("run_name", "")).strip() or None
    except Exception:
        return None


def _latest_campaign_logs() -> List[Path]:
    if not LOG_DIR.is_dir():
        return []
    return sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]


def _tail_text(path: Path, nbytes: int = 12000) -> str:
    if not path.is_file():
        return ""
    data = path.read_bytes()
    return (data if len(data) <= nbytes else data[-nbytes:]).decode("utf-8", errors="replace")


def _scan_logs_for_issues(logs: List[Path], *, max_age_sec: int = 1800) -> Tuple[bool, bool, str, bool]:
    oom = crash = oom_recent = False
    detail = ""
    now = datetime.now(timezone.utc).timestamp()
    for log in logs:
        try:
            age = now - log.stat().st_mtime
        except OSError:
            age = 999999
        tail = _tail_text(log)
        for pat in OOM_PATTERNS:
            if pat.lower() in tail.lower():
                oom = True
                detail = f"OOM in {log.name}"
                if age <= max_age_sec:
                    oom_recent = True
                break
        for pat in CRASH_PATTERNS:
            if pat in tail:
                crash = True
                if not detail:
                    detail = f"crash in {log.name}"
                break
        if oom:
            break
    return oom, crash, detail, oom_recent


def _segment_stuck(active_run: Optional[str]) -> bool:
    if not active_run:
        return False
    run_dir = _run_dir_for_row({"run_name": active_run})
    metrics = run_dir / "metrics.jsonl"
    if metrics.is_file():
        try:
            age = datetime.now(timezone.utc).timestamp() - metrics.stat().st_mtime
            return age > STUCK_SEGMENT_SEC
        except OSError:
            pass
    segments = sorted(run_dir.glob("segment_*"))
    if segments:
        try:
            age = datetime.now(timezone.utc).timestamp() - segments[-1].stat().st_mtime
            return age > STUCK_SEGMENT_SEC
        except OSError:
            pass
    return False


def _kill_train_pids(pids: List[int]) -> List[int]:
    killed: List[int] = []
    for pid in pids:
        try:
            subprocess.run(["kill", str(pid)], check=False)
            killed.append(pid)
        except OSError:
            pass
    return killed


def _kill_parallel_tmux(sessions: List[str]) -> List[str]:
    killed: List[str] = []
    for sess in PARALLEL_SESSIONS:
        if sess in sessions:
            subprocess.run(["tmux", "kill-session", "-t", sess], check=False)
            killed.append(sess)
            _log(f"AUTO_FIX killed parallel tmux {sess}")
    return killed


def _relaunch_serial() -> bool:
    if not SERIAL_LAUNCH_SCRIPT.is_file():
        _log(f"BLOCKED relaunch: missing {SERIAL_LAUNCH_SCRIPT}")
        return False
    subprocess.run(["bash", str(SERIAL_LAUNCH_SCRIPT)], cwd=str(REPO), check=False)
    _log(f"AUTO_FIX relaunched serial via {SERIAL_LAUNCH_SCRIPT.name}")
    return True


def _active_campaign_tmux(sessions: List[str]) -> Optional[str]:
    for name in CAMPAIGN_TRAINING_SESSIONS:
        if name in sessions:
            return name
    return None


def main() -> int:
    SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    state = _load_state()
    issues: List[str] = []
    auto_fixes: List[str] = []
    wake_issue: Optional[str] = None
    wake_report: Optional[str] = None

    sessions = _tmux_sessions()
    procs = _refine_campaign_flags(_train_processes())
    campaign_procs = [p for p in procs if p["is_campaign"]]
    other_procs = [p for p in procs if not p["is_campaign"]]
    campaign_tmux = _active_campaign_tmux(sessions)
    gpu = _gpu_stats()

    active_run: Optional[str] = None
    if campaign_procs:
        active_run = _parse_run_from_train(campaign_procs[0]["cmd"])

    rows = _read_manifest()
    manifest_counts, failed_rows = _manifest_progress(rows, active_run)
    campaign_done = manifest_counts["completed"] >= manifest_counts["total"]

    _log(
        f"TICK tmux={campaign_tmux or 'none'} train={len(procs)} campaign_train={len(campaign_procs)} "
        f"manifest={manifest_counts['completed']}/{manifest_counts['total']} run={active_run or '—'}"
    )

    if gpu:
        mem_pct = gpu.get("memory_pct", 0)
        if len(procs) == 0 and mem_pct > 85:
            issues.append(f"GPU 显存 {mem_pct}% 但无 train.py")
        elif len(procs) >= 1 and mem_pct > 97:
            issues.append(f"GPU 显存临界 {mem_pct}%")

    if len(procs) > 1:
        issues.append(f"多个 train.py ({len(procs)}) — OOM 风险")
        sorted_procs = sorted(procs, key=lambda p: p["pid"], reverse=True)
        keep = sorted_procs[0]
        extras = [p["pid"] for p in sorted_procs[1:]]
        killed = _kill_train_pids(extras)
        if killed:
            auto_fixes.append(f"已杀掉多余 train.py pids={killed}，保留 pid={keep['pid']}")
            wake_issue = f"多 train 进程已清理 pids={killed}，请确认串行模式"

    parallel_alive = [s for s in sessions if s in PARALLEL_SESSIONS]
    if len(parallel_alive) >= 2 or (parallel_alive and len(campaign_procs) > 1):
        killed_sess = _kill_parallel_tmux(sessions)
        if killed_sess:
            auto_fixes.append(f"已杀掉并行 tmux: {killed_sess}")
            issues.append("检测到并行 campaign tmux")
            wake_issue = wake_issue or "并行 tmux 已清理，请确认仅 serial 运行"

    logs = _latest_campaign_logs()
    oom_hit, crash_hit, log_detail, oom_recent = _scan_logs_for_issues(logs)
    if oom_hit and oom_recent:
        issues.append(log_detail or "campaign 日志 OOM")
        state["last_oom"] = _now()
        killed_sess = _kill_parallel_tmux(sessions)
        if killed_sess:
            auto_fixes.append(f"OOM 后杀掉并行 tmux: {killed_sess}")
        wake_issue = wake_issue or (log_detail or "OOM 需 Agent 分析 config")
    elif crash_hit and not campaign_procs:
        issues.append(log_detail or "campaign 日志崩溃")
        wake_issue = wake_issue or log_detail or "训练崩溃需诊断"

    priority_active = "v8s5camp_priority" in sessions
    if not campaign_tmux and not campaign_done and not campaign_procs and not priority_active:
        issues.append("campaign tmux 已死且 manifest 未完成")
        if _relaunch_serial():
            auto_fixes.append("已重启 v8s5camp_serial")
        else:
            wake_issue = wake_issue or "tmux 死亡且 serial 重启失败"

    elif campaign_tmux and not campaign_procs and not campaign_done:
        manifest_runner = False
        try:
            out = subprocess.check_output(["pgrep", "-af", "run_from_manifest"], text=True)
            manifest_runner = any("run_from_manifest.py" in ln for ln in out.splitlines())
        except subprocess.CalledProcessError:
            pass
        if not manifest_runner:
            issues.append("tmux 存活但无 train.py 且无 manifest runner")
            if campaign_tmux != PREFERRED_SERIAL_SESSION and PREFERRED_SERIAL_SESSION not in sessions:
                if _relaunch_serial():
                    auto_fixes.append("停滞 tmux 已重启 serial")
                else:
                    wake_issue = wake_issue or f"会话 {campaign_tmux} 停滞"
            else:
                wake_issue = wake_issue or f"会话 {campaign_tmux} 空闲无 train.py"

    if active_run and _segment_stuck(active_run) and campaign_procs:
        issues.append(f"segment 可能卡住 >{STUCK_SEGMENT_SEC // 60}min: {active_run}")
        wake_issue = wake_issue or f"segment 停滞 {active_run}"

    if other_procs and campaign_procs:
        issues.append(f"非 campaign train ({len(other_procs)}) 与 campaign 并存")
        wake_issue = wake_issue or "GPU 冲突：campaign 与非 campaign 同时训练"

    if len(failed_rows) >= 3 and not campaign_procs:
        issues.append(f"{len(failed_rows)} 个失败 run 无 final_metrics")
        wake_issue = wake_issue or f"{len(failed_rows)} 个失败 run 待重试/诊断"

    prev_completed_list = list(state.get("completed_runs") or [])
    cur_completed_list = _completed_runs(rows)
    prev_completed = len(prev_completed_list) if prev_completed_list else int(
        (state.get("manifest") or {}).get("completed", 0)
    )
    milestone = manifest_counts["completed"] > prev_completed
    latest_run = _latest_completed_run(prev_completed_list, cur_completed_list)
    if milestone and latest_run:
        metrics_path = REPO / "results/runs" / latest_run / "final_metrics.json"
        wake_report = (
            f"run 完成 `{latest_run}`，进度 {manifest_counts['completed']}/{manifest_counts['total']}，"
            f"metrics={metrics_path}"
        )
    elif milestone:
        wake_report = f"run 完成，进度 {manifest_counts['completed']}/{manifest_counts['total']}"

    phase1_wake = False
    if _phase_complete(rows, "1") and not state.get("phase1_complete_reported"):
        phase1_rows = [r for r in rows if str(r.get("phase", "")).strip() == "1"]
        if phase1_rows:
            rn = phase1_rows[0]["run_name"].strip()
            metrics_path = REPO / "results/runs" / rn / "final_metrics.json"
            wake_report = wake_report or (
                f"Phase1 全部完成，metrics={metrics_path}，进度 "
                f"{manifest_counts['completed']}/{manifest_counts['total']}"
            )
            phase1_wake = True
            state["phase1_complete_reported"] = True

    priority_state_path = CAMPAIGN_DIR / "PRIORITY_QUEUE.state"
    if priority_state_path.is_file():
        try:
            pq = json.loads(priority_state_path.read_text(encoding="utf-8"))
            if pq.get("status") == "completed" and state.get("last_priority_done") != pq.get("completed_at"):
                wake_report = wake_report or "优先队列任务已完成"
                state["last_priority_done"] = pq.get("completed_at")
        except json.JSONDecodeError:
            pass

    healthy = campaign_procs and len(campaign_procs) == 1 and campaign_tmux and len(procs) <= 1
    if healthy and not issues:
        state["pending_agent"] = None
        state["pending_action"] = None
    elif wake_issue:
        state["pending_agent"] = wake_issue
        state["pending_action"] = "fix"
        _invoke_wake(reason="issue", message=wake_issue)
    elif wake_report:
        state["pending_action"] = "report"
        report_reason = "milestone" if (milestone or phase1_wake) else "report"
        _invoke_wake(reason=report_reason, message=wake_report)

    state["completed_runs"] = cur_completed_list
    state["campaign_tmux_alive"] = bool(campaign_tmux)
    state["train_count"] = len(procs)
    state["campaign_train_count"] = len(campaign_procs)
    state["manifest"] = manifest_counts
    state["current_run"] = active_run
    state["gpu"] = gpu
    state["campaign_tmux"] = campaign_tmux
    state["issues"] = issues
    state["auto_fixes"] = auto_fixes
    _save_state(state)
    _run_status_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
