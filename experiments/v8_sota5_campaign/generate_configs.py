#!/usr/bin/env python3
"""Generate v8_sota5 campaign configs and phased manifest.csv (phases 1-4)."""
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
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from run_ours_mini_ablation import ABLATIONS  # noqa: E402


WANDB_PROJECT = "lora-citb-v8-sota5-paper"
CAMPAIGN_TAG = "v8_sota5_campaign"
CHAMPION_TAG = "v8_sota_5"
CHAMPION_VARIANT = "v8_sota_5"
CHAMPION_MODULES_KEY = "ours_full"

ABLATION_VARIANTS = [
    CHAMPION_VARIANT,
    "ours_no_drift",
    "ours_no_bank",
    "ours_no_router",
    "ours_no_overlap",
]

CHAMPION_ROUTER_ASSERTIONS = {
    "routing_backend": "prototype",
    "spawn_sync_prototype_init": True,
    "prototype_update_steps": 3,
}

BASELINE_VARIANTS = [
    "seq",
    "replay_b50",
    "periodic_latest",
    "bank_no_router",
    "router_only",
]

PHASE_BY_CATEGORY = {
    "phase1_priority": 1,
    "ablation_single_seed": 3,
    "baseline_multiseed": 2,
    "ours_multiseed": 4,
}

DEFAULT_SEEDS = [123, 456, 789]
DEFAULT_BENCHMARKS = ["instrdialog", "instrdialog++"]


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _validate_champion_base(cfg: Dict[str, Any], path: Path) -> None:
    router = cfg.get("router", {})
    if not isinstance(router, dict):
        raise ValueError(f"Base config missing router section: {path}")
    for key, expected in CHAMPION_ROUTER_ASSERTIONS.items():
        actual = router.get(key)
        if actual != expected:
            raise ValueError(
                f"Base config {path} is not v8_sota_5 champion: "
                f"router.{key}={actual!r}, expected {expected!r}. "
                "Use configs/paper/v8_sota_5.yaml — not instrdialog*__ours_full__*.yaml."
            )


def _modules_for_variant(variant: str) -> Dict[str, Any]:
    key = CHAMPION_MODULES_KEY if variant == CHAMPION_VARIANT else variant
    if key not in ABLATIONS:
        raise ValueError(f"Unknown ablation variant: {variant}")
    return ABLATIONS[key]


def _champion_run_name(benchmark_slug: str, seed: int, *, suffix: str) -> str:
    return f"paper_{benchmark_slug}_v8_sota5_ours_s{seed}_{suffix}"


def _slug(text: str) -> str:
    out = text.strip().lower()
    out = out.replace("++", "pp")
    out = out.replace("+", "p")
    out = out.replace("/", "_")
    out = out.replace(" ", "_")
    return out


def _ensure_mapping(parent: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = parent.setdefault(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at key '{key}'")
    return value


def _set_stream(cfg: Dict[str, Any], benchmark: str) -> None:
    data_cfg = _ensure_mapping(cfg, "data")
    data_cfg["stream_name"] = benchmark
    data_cfg["auto_prepare_processed"] = True


def _apply_tracking(
    cfg: Dict[str, Any],
    *,
    wandb_group: str,
    tags: List[str],
    notes: str,
) -> None:
    output_cfg = _ensure_mapping(cfg, "output")
    tracking = _ensure_mapping(output_cfg, "tracking")
    tracking["use_wandb"] = True
    tracking["wandb_project"] = WANDB_PROJECT
    tracking["wandb_group"] = wandb_group
    tracking["wandb_tags"] = tags
    tracking["wandb_mode"] = "online"
    tracking["wandb_notes"] = notes


def _apply_paper_meta(
    cfg: Dict[str, Any],
    *,
    benchmark: str,
    category: str,
    method_variant: str,
    seed: int,
    run_name: str,
) -> None:
    cfg["seed"] = int(seed)
    cfg["experiment_name"] = f"paper_ours_{_slug(benchmark)}"
    output_cfg = _ensure_mapping(cfg, "output")
    output_cfg["run_name"] = run_name
    paper_cfg = _ensure_mapping(cfg, "paper")
    paper_cfg["track"] = "paper"
    paper_cfg["category"] = category
    paper_cfg["family"] = "ours"
    paper_cfg["benchmark_alias"] = benchmark
    paper_cfg["method_variant"] = method_variant
    paper_cfg["memory_budget"] = 0


def _base_tags(*, category: str, benchmark: str, seed: int, variant: str) -> List[str]:
    return [
        CAMPAIGN_TAG,
        CHAMPION_TAG,
        category,
        _slug(benchmark),
        f"seed_{seed}",
        variant,
    ]


def _write_yaml(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)


def _manifest_row(
    *,
    phase: int,
    category: str,
    benchmark: str,
    seed: int,
    variant_id: str,
    mode: str,
    run_name: str,
    config_path: str,
    wandb_group: str,
    wandb_tags: List[str],
    run_name_suffix: str = "",
    config_source: str = "generated",
) -> Dict[str, Any]:
    return {
        "phase": int(phase),
        "category": category,
        "benchmark": benchmark,
        "benchmark_slug": _slug(benchmark),
        "seed": int(seed),
        "variant_id": variant_id,
        "mode": mode,
        "run_name": run_name,
        "config_path": config_path,
        "wandb_project": WANDB_PROJECT,
        "wandb_group": wandb_group,
        "wandb_tags": "|".join(wandb_tags),
        "run_name_suffix": run_name_suffix,
        "config_source": config_source,
    }


def _write_champion_config(
    base_cfg: Dict[str, Any],
    *,
    output_dir: Path,
    subdir: str,
    benchmark: str,
    seed: int,
    category: str,
    wandb_group: str,
    tags: List[str],
    notes: str,
    run_name: str,
) -> str:
    cfg = copy.deepcopy(base_cfg)
    _set_stream(cfg, benchmark)
    modules_cfg = _ensure_mapping(cfg, "modules")
    modules_cfg.update(_modules_for_variant(CHAMPION_VARIANT))
    _apply_paper_meta(
        cfg,
        benchmark=benchmark,
        category=category,
        method_variant=CHAMPION_VARIANT,
        seed=seed,
        run_name=run_name,
    )
    _apply_tracking(cfg, wandb_group=wandb_group, tags=tags, notes=notes)
    benchmark_slug = _slug(benchmark)
    rel_path = output_dir / subdir / f"{benchmark_slug}__{CHAMPION_VARIANT}__s{seed}.yaml"
    _write_yaml(rel_path, cfg)
    return str(rel_path.relative_to(REPO_ROOT))


def generate_phase1_priority(
    base_cfg: Dict[str, Any],
    *,
    output_dir: Path,
    seed: int,
    benchmark: str,
) -> List[Dict[str, Any]]:
    benchmark_slug = _slug(benchmark)
    run_name = _champion_run_name(benchmark_slug, seed, suffix="v8s5camp")
    tags = _base_tags(
        category="phase1_priority",
        benchmark=benchmark,
        seed=seed,
        variant=CHAMPION_VARIANT,
    )
    config_path = _write_champion_config(
        base_cfg,
        output_dir=output_dir,
        subdir="phase1",
        benchmark=benchmark,
        seed=seed,
        category="priority",
        wandb_group="phase1_priority_instrdialogpp",
        tags=tags,
        notes=f"Phase 1: v8_sota_5 champion priority ({benchmark}, seed={seed})",
        run_name=run_name,
    )
    return [
        _manifest_row(
            phase=1,
            category="phase1_priority",
            benchmark=benchmark,
            seed=seed,
            variant_id=CHAMPION_VARIANT,
            mode="ours",
            run_name=run_name,
            config_path=config_path,
            wandb_group="phase1_priority_instrdialogpp",
            wandb_tags=tags,
        )
    ]


def generate_ablation_configs(
    base_cfg: Dict[str, Any],
    *,
    output_dir: Path,
    seed: int,
    benchmarks: List[str],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    wandb_group = "ablation_single_seed"

    for benchmark in benchmarks:
        benchmark_slug = _slug(benchmark)
        for variant in ABLATION_VARIANTS:
            cfg = copy.deepcopy(base_cfg)
            _set_stream(cfg, benchmark)
            modules_cfg = _ensure_mapping(cfg, "modules")
            modules_cfg.update(_modules_for_variant(variant))

            if variant == CHAMPION_VARIANT:
                run_name = _champion_run_name(benchmark_slug, seed, suffix="v8s5camp")
            else:
                run_name = f"paper_{benchmark_slug}_{variant}_s{seed}_v8s5camp"
            method_variant = CHAMPION_VARIANT if variant == CHAMPION_VARIANT else variant
            _apply_paper_meta(
                cfg,
                benchmark=benchmark,
                category="ablation",
                method_variant=method_variant,
                seed=seed,
                run_name=run_name,
            )
            tags = _base_tags(
                category="ablation_single_seed",
                benchmark=benchmark,
                seed=seed,
                variant=variant,
            )
            _apply_tracking(
                cfg,
                wandb_group=wandb_group,
                tags=tags,
                notes=(
                    f"Phase 2: v8_sota_5 ablation ({variant}, seed={seed}, {benchmark})"
                    + (" — champion full config" if variant == CHAMPION_VARIANT else "")
                ),
            )

            rel_path = output_dir / "ablation" / f"{benchmark_slug}__{variant}__s{seed}.yaml"
            _write_yaml(rel_path, cfg)
            rows.append(
                _manifest_row(
                    phase=2,
                    category="ablation_single_seed",
                    benchmark=benchmark,
                    seed=seed,
                    variant_id=variant,
                    mode="ours",
                    run_name=run_name,
                    config_path=str(rel_path.relative_to(REPO_ROOT)),
                    wandb_group=wandb_group,
                    wandb_tags=tags,
                )
            )
    return rows


def generate_ours_multiseed_configs(
    base_cfg: Dict[str, Any],
    *,
    output_dir: Path,
    seeds: List[int],
    benchmarks: List[str],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    variant = CHAMPION_VARIANT

    for benchmark in benchmarks:
        benchmark_slug = _slug(benchmark)
        wandb_group = (
            "ours_multiseed_instrdialog"
            if benchmark == "instrdialog"
            else "ours_multiseed_instrdialogpp"
        )
        for seed in seeds:
            run_name = _champion_run_name(benchmark_slug, seed, suffix="v8s5camp")
            tags = _base_tags(
                category="ours_multiseed",
                benchmark=benchmark,
                seed=seed,
                variant=variant,
            )
            config_path = _write_champion_config(
                base_cfg,
                output_dir=output_dir,
                subdir="ours_multiseed",
                benchmark=benchmark,
                seed=seed,
                category="main",
                wandb_group=wandb_group,
                tags=tags,
                notes=f"Phase 4: v8_sota_5 champion multi-seed ({benchmark}, seed={seed})",
                run_name=run_name,
            )
            rows.append(
                _manifest_row(
                    phase=4,
                    category="ours_multiseed",
                    benchmark=benchmark,
                    seed=seed,
                    variant_id=variant,
                    mode="ours",
                    run_name=run_name,
                    config_path=config_path,
                    wandb_group=wandb_group,
                    wandb_tags=tags,
                )
            )
    return rows


def generate_baseline_manifest_entries(
    *,
    seeds: List[int],
    benchmarks: List[str],
    run_suffix: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for benchmark in benchmarks:
        benchmark_slug = _slug(benchmark)
        wandb_group = (
            "baseline_multiseed_instrdialog"
            if benchmark == "instrdialog"
            else "baseline_multiseed_instrdialogpp"
        )
        for seed in seeds:
            for variant in BASELINE_VARIANTS:
                config_path = REPO_ROOT / "configs" / "paper" / f"{benchmark_slug}__{variant}__s{seed}.yaml"
                if not config_path.is_file():
                    raise FileNotFoundError(f"Missing baseline config: {config_path}")

                base_cfg = _load_yaml(config_path)
                base_run_name = str(base_cfg.get("output", {}).get("run_name", "")).strip()
                run_name = f"{base_run_name}_{run_suffix}" if run_suffix else base_run_name
                tags = _base_tags(
                    category="baseline_multiseed",
                    benchmark=benchmark,
                    seed=seed,
                    variant=variant,
                )

                rows.append(
                    _manifest_row(
                        phase=3,
                        category="baseline_multiseed",
                        benchmark=benchmark,
                        seed=seed,
                        variant_id=variant,
                        mode="baseline",
                        run_name=run_name,
                        config_path=str(config_path.relative_to(REPO_ROOT)),
                        wandb_group=wandb_group,
                        wandb_tags=tags,
                        run_name_suffix=run_suffix,
                        config_source="existing_paper_matrix",
                    )
                )
    return rows


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate v8_sota5 phased campaign configs and manifest.")
    parser.add_argument(
        "--base-config",
        type=Path,
        default=Path("configs/paper/v8_sota_5.yaml"),
        help="Champion v8_sota_5 YAML template.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("configs/paper/v8_sota5_campaign"),
        help="Directory for generated configs.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("experiments/v8_sota5_campaign/manifest.csv"),
        help="Campaign manifest CSV path.",
    )
    parser.add_argument("--phase1-seed", type=int, default=123)
    parser.add_argument("--phase1-benchmark", type=str, default="instrdialog++")
    parser.add_argument("--ablation-seed", type=int, default=123)
    parser.add_argument("--ablation-benchmarks", type=str, default="instrdialog,instrdialog++")
    parser.add_argument("--seeds", type=str, default="123,456,789")
    parser.add_argument("--benchmarks", type=str, default="instrdialog,instrdialog++")
    parser.add_argument("--run-suffix", type=str, default="v8s5camp")
    args = parser.parse_args()

    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    benchmarks = [x.strip() for x in args.benchmarks.split(",") if x.strip()]
    ablation_benchmarks = [x.strip() for x in args.ablation_benchmarks.split(",") if x.strip()]

    base_config_path = (REPO_ROOT / args.base_config).resolve()
    base_cfg = _load_yaml(base_config_path)
    _validate_champion_base(base_cfg, base_config_path)
    output_dir = (REPO_ROOT / args.output_dir).resolve()

    rows: List[Dict[str, Any]] = []
    rows.extend(
        generate_phase1_priority(
            base_cfg,
            output_dir=output_dir,
            seed=args.phase1_seed,
            benchmark=args.phase1_benchmark,
        )
    )
    rows.extend(
        generate_ablation_configs(
            base_cfg,
            output_dir=output_dir,
            seed=args.ablation_seed,
            benchmarks=ablation_benchmarks,
        )
    )
    rows.extend(
        generate_baseline_manifest_entries(
            seeds=seeds,
            benchmarks=benchmarks,
            run_suffix=args.run_suffix.strip(),
        )
    )
    rows.extend(
        generate_ours_multiseed_configs(
            base_cfg,
            output_dir=output_dir,
            seeds=seeds,
            benchmarks=benchmarks,
        )
    )

    rows.sort(
        key=lambda r: (
            int(r["phase"]),
            r["benchmark_slug"],
            r["variant_id"],
            int(r["seed"]),
        )
    )
    manifest_path = (REPO_ROOT / args.manifest).resolve()
    _write_csv(manifest_path, rows)

    by_phase: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for row in rows:
        phase_key = f"phase_{row['phase']}"
        by_phase[phase_key] = by_phase.get(phase_key, 0) + 1
        cat = row["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    summary = {
        "total_runs": len(rows),
        "by_phase": by_phase,
        "by_category": by_category,
        "execution_order": [
            "phase1_priority (1)",
            "ablation_single_seed (10)",
            "baseline_multiseed (30)",
            "ours_multiseed (6)",
        ],
        "wandb_project": WANDB_PROJECT,
        "output_dir": str(output_dir.relative_to(REPO_ROOT)),
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
    }
    summary_path = manifest_path.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
