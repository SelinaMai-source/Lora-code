#!/usr/bin/env python3
"""Generate v7 SOTA search grid: 12 configs (2×2 drift × 3 router bundles)."""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

WANDB_PROJECT = "lora-citb-v7-sota"
WANDB_GROUP = "v7_search_phase1"
BASE_CONFIG = REPO_ROOT / "configs/paper/v8_sota_5.yaml"
TEMPLATE = REPO_ROOT / "configs/paper/v7_sota_template.yaml"
OUTPUT_DIR = REPO_ROOT / "configs/paper/v7_sota"

# 2×2 drift: threshold × anchor_size (refresh 与 anchor 配对)
DRIFT_GRID = [
    {"threshold": 0.025, "anchor_size": 64, "anchor_refresh_segments": 1},
    {"threshold": 0.020, "anchor_size": 64, "anchor_refresh_segments": 1},
    {"threshold": 0.025, "anchor_size": 32, "anchor_refresh_segments": 2},
    {"threshold": 0.020, "anchor_size": 32, "anchor_refresh_segments": 2},
]

# 3 router/branch bundles（沿用 v8 线典型配对）
ROUTER_BUNDLES = [
    {
        "id": "lean",
        "max_branches": 12,
        "prototype_update_steps": 2,
        "spawn_sync_prototype_init": True,
        "prototype_ema": 0.8,
        "note": "紧分支预算 + 双步 prototype 更新",
    },
    {
        "id": "champion",
        "max_branches": 15,
        "prototype_update_steps": 3,
        "spawn_sync_prototype_init": True,
        "prototype_ema": 0.8,
        "note": "v8_sota_5 冠军 router/branch 配对",
    },
    {
        "id": "slow_ema",
        "max_branches": 15,
        "prototype_update_steps": 2,
        "spawn_sync_prototype_init": True,
        "prototype_ema": 0.9,
        "note": "较高 prototype EMA（v8_sota_9 方向）",
    },
]


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping: {path}")
    return data


def _ensure_mapping(parent: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = parent.setdefault(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at '{key}'")
    return value


def _validate_champion_base(cfg: Dict[str, Any]) -> None:
    router = cfg.get("router", {})
    if router.get("routing_backend") != "prototype":
        raise ValueError("Base must use prototype routing_backend (v8_sota_5 line)")


def _build_combo_index(drift_idx: int, router_idx: int) -> int:
    return drift_idx * len(ROUTER_BUNDLES) + router_idx + 1


def generate_configs(*, benchmark: str = "instrdialog", seed: int = 123) -> List[Dict[str, Any]]:
    base = _load_yaml(BASE_CONFIG)
    _validate_champion_base(base)

    rows: List[Dict[str, Any]] = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for d_i, drift in enumerate(DRIFT_GRID):
        for r_i, bundle in enumerate(ROUTER_BUNDLES):
            idx = _build_combo_index(d_i, r_i)
            cfg_id = f"v7_sota_{idx:02d}"
            run_name = f"{cfg_id}_{benchmark}_s{seed}"

            cfg = copy.deepcopy(base)
            data_cfg = _ensure_mapping(cfg, "data")
            data_cfg["stream_name"] = benchmark
            data_cfg["auto_prepare_processed"] = True

            drift_cfg = _ensure_mapping(cfg, "drift")
            drift_cfg.update(
                {
                    "threshold": drift["threshold"],
                    "anchor_size": drift["anchor_size"],
                    "anchor_refresh_segments": drift["anchor_refresh_segments"],
                }
            )

            bank_cfg = _ensure_mapping(cfg, "bank")
            bank_cfg["max_branches"] = bundle["max_branches"]

            router_cfg = _ensure_mapping(cfg, "router")
            router_cfg.update(
                {
                    "prototype_update_steps": bundle["prototype_update_steps"],
                    "spawn_sync_prototype_init": bundle["spawn_sync_prototype_init"],
                    "prototype_ema": bundle["prototype_ema"],
                    "routing_backend": "prototype",
                }
            )

            cfg["seed"] = seed
            output_cfg = _ensure_mapping(cfg, "output")
            output_cfg["run_name"] = run_name
            tracking = _ensure_mapping(output_cfg, "tracking")
            tracking["use_wandb"] = True
            tracking["wandb_project"] = WANDB_PROJECT
            tracking["wandb_group"] = WANDB_GROUP
            tracking["wandb_mode"] = "online"
            tags = [
                "v7_sota",
                "v7_search_phase1",
                cfg_id,
                f"drift_t{drift['threshold']}",
                f"anchor_{drift['anchor_size']}",
                f"refresh_{drift['anchor_refresh_segments']}",
                f"branches_{bundle['max_branches']}",
                f"proto_steps_{bundle['prototype_update_steps']}",
                f"bundle_{bundle['id']}",
                f"seed_{seed}",
                benchmark,
            ]
            tracking["wandb_tags"] = tags
            tracking["wandb_notes"] = (
                f"{cfg_id}: drift(th={drift['threshold']}, anchor={drift['anchor_size']}, "
                f"refresh={drift['anchor_refresh_segments']}); "
                f"router(mb={bundle['max_branches']}, steps={bundle['prototype_update_steps']}, "
                f"ema={bundle['prototype_ema']}, sync={bundle['spawn_sync_prototype_init']}). "
                f"{bundle['note']}"
            )

            paper_cfg = _ensure_mapping(cfg, "paper")
            paper_cfg["category"] = "search"
            paper_cfg["method_variant"] = cfg_id
            paper_cfg["benchmark_alias"] = benchmark

            rel_path = OUTPUT_DIR / f"{cfg_id}.yaml"
            with rel_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

            rows.append(
                {
                    "index": idx,
                    "config_id": cfg_id,
                    "benchmark": benchmark,
                    "seed": seed,
                    "run_name": run_name,
                    "config_path": str(rel_path.relative_to(REPO_ROOT)),
                    "wandb_project": WANDB_PROJECT,
                    "wandb_group": WANDB_GROUP,
                    "drift_threshold": drift["threshold"],
                    "anchor_size": drift["anchor_size"],
                    "anchor_refresh_segments": drift["anchor_refresh_segments"],
                    "max_branches": bundle["max_branches"],
                    "prototype_update_steps": bundle["prototype_update_steps"],
                    "prototype_ema": bundle["prototype_ema"],
                    "spawn_sync_prototype_init": bundle["spawn_sync_prototype_init"],
                    "router_bundle": bundle["id"],
                }
            )

    return rows


def _write_manifest(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate v7 SOTA 12-combo search space.")
    parser.add_argument("--benchmark", default="instrdialog")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("experiments/v7_sota_campaign/manifest_phase1.csv"),
    )
    args = parser.parse_args()

    rows = generate_configs(benchmark=args.benchmark, seed=args.seed)
    manifest_path = (REPO_ROOT / args.manifest).resolve()
    _write_manifest(rows, manifest_path)

    summary = {
        "total_configs": len(rows),
        "grid": "2×2 drift × 3 router bundles = 12",
        "wandb_project": WANDB_PROJECT,
        "output_dir": str(OUTPUT_DIR.relative_to(REPO_ROOT)),
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        "configs": [r["config_id"] for r in rows],
    }
    summary_path = manifest_path.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
