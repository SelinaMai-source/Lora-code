#!/usr/bin/env python3
"""Execute v8_sota5 campaign runs from manifest.csv."""
from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WANDB_PROJECT = "lora-citb-v8-sota5-paper"


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _ensure_mapping(parent: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = parent.setdefault(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at key '{key}'")
    return value


def _apply_manifest_overrides(cfg: Dict[str, Any], row: Dict[str, str]) -> str:
    output_cfg = _ensure_mapping(cfg, "output")
    suffix = str(row.get("run_name_suffix", "")).strip()
    base_run_name = str(output_cfg.get("run_name", "")).strip()
    if suffix and not base_run_name.endswith(f"_{suffix}"):
        output_cfg["run_name"] = f"{base_run_name}_{suffix}"
    elif row.get("run_name"):
        output_cfg["run_name"] = str(row["run_name"]).strip()

    run_name = str(output_cfg.get("run_name", "")).strip()

    tracking = _ensure_mapping(output_cfg, "tracking")
    tracking["use_wandb"] = True
    project = (
        str(row.get("wandb_project", "")).strip()
        or str(os.environ.get("WANDB_PROJECT", "")).strip()
        or DEFAULT_WANDB_PROJECT
    )
    tracking["wandb_project"] = project
    if row.get("wandb_group"):
        tracking["wandb_group"] = str(row["wandb_group"]).strip()
    tags_raw = str(row.get("wandb_tags", "")).strip()
    if tags_raw:
        tracking["wandb_tags"] = [t for t in tags_raw.split("|") if t]
    wandb_mode = str(os.environ.get("WANDB_MODE", "online")).strip() or "online"
    if wandb_mode == "disabled":
        raise RuntimeError(
            "WANDB_MODE=disabled blocks campaign logging. "
            f"Unset it or set WANDB_MODE=online (required project: {DEFAULT_WANDB_PROJECT})."
        )
    tracking["wandb_mode"] = wandb_mode

    return run_name


def _select_rows(
    rows: List[Dict[str, str]],
    categories: List[str],
    phases: List[str],
) -> List[Dict[str, str]]:
    selected = rows
    if categories:
        allowed = set(categories)
        selected = [row for row in selected if row.get("category", "") in allowed]
    if phases:
        allowed_phases = set(phases)
        selected = [row for row in selected if str(row.get("phase", "")).strip() in allowed_phases]
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v8_sota5 campaign entries from manifest.csv.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("experiments/v8_sota5_campaign/manifest.csv"),
    )
    parser.add_argument(
        "--categories",
        type=str,
        default="",
        help="Comma-separated category filter (e.g. ablation_single_seed,ours_multiseed).",
    )
    parser.add_argument(
        "--phases",
        type=str,
        default="",
        help="Comma-separated phase filter (1=phase1_priority, 2=baselines, 3=ablation, 4=ours).",
    )
    parser.add_argument(
        "--variant-ids",
        type=str,
        default="",
        help="Optional comma-separated variant_id filter.",
    )
    parser.add_argument(
        "--benchmarks",
        type=str,
        default="",
        help="Optional comma-separated benchmark filter.",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="",
        help="Optional comma-separated seed filter.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip runs whose final_metrics.json already exists.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="On train.py failure, log and continue to the next manifest row (failed runs retry on next pass).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected runs without executing train.py.",
    )
    args = parser.parse_args()

    manifest_path = (REPO_ROOT / args.manifest).resolve()
    rows = _read_csv(manifest_path)
    categories = [x.strip() for x in args.categories.split(",") if x.strip()]
    phases = [x.strip() for x in args.phases.split(",") if x.strip()]
    variant_ids = [x.strip() for x in args.variant_ids.split(",") if x.strip()]
    benchmarks = [x.strip() for x in args.benchmarks.split(",") if x.strip()]
    seeds = [x.strip() for x in args.seeds.split(",") if x.strip()]

    selected = _select_rows(rows, categories, phases)
    if variant_ids:
        selected = [r for r in selected if r.get("variant_id", "") in set(variant_ids)]
    if benchmarks:
        selected = [r for r in selected if r.get("benchmark", "") in set(benchmarks)]
    if seeds:
        selected = [r for r in selected if str(r.get("seed", "")) in set(seeds)]

    if not selected:
        raise ValueError("No manifest rows matched the requested filters.")

    executed = 0
    skipped = 0
    for row in selected:
        cfg_path = (REPO_ROOT / row["config_path"]).resolve()
        cfg = _load_yaml(cfg_path)
        run_name = _apply_manifest_overrides(cfg, row)
        tracking = (cfg.get("output") or {}).get("tracking") or {}

        results_dir = str(cfg.get("paths", {}).get("results_dir", "results"))
        final_metrics_path = REPO_ROOT / results_dir / "runs" / run_name / "final_metrics.json"

        if args.skip_existing and final_metrics_path.is_file():
            print(f"[skip-existing] {run_name}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"[dry-run] {run_name} <- {row['config_path']} group={row.get('wandb_group', '')}")
            continue

        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
            yaml.safe_dump(cfg, tmp, sort_keys=False, allow_unicode=True)
            tmp_path = Path(tmp.name)

        print(f"[run] {run_name} <- {row['config_path']}")
        train_env = os.environ.copy()
        train_env.setdefault("WANDB_PROJECT", tracking.get("wandb_project", DEFAULT_WANDB_PROJECT))
        train_env.setdefault("WANDB_MODE", tracking.get("wandb_mode", "online"))
        try:
            result = subprocess.run(
                [sys.executable, "core/train.py", "--config", str(tmp_path)],
                cwd=REPO_ROOT,
                env=train_env,
                check=False,
            )
            if result.returncode == 0:
                executed += 1
            elif args.continue_on_error:
                print(f"[error-continue] {run_name} exit={result.returncode}", file=sys.stderr)
            else:
                raise subprocess.CalledProcessError(result.returncode, result.args)
        finally:
            tmp_path.unlink(missing_ok=True)

    print(f"[done] executed={executed} skipped={skipped} selected={len(selected)}")


if __name__ == "__main__":
    main()
