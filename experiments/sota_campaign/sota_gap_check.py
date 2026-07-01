#!/usr/bin/env python3
"""Check Ours metrics vs +10% CL SOTA targets (three suites). Exit 0 if all pass."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO / "experiments" / "sota_campaign"

# Higher-is-better targets from SOTA_GAP_TRACKER.md (baseline * 1.10)
TARGETS: Dict[str, Dict[str, Tuple[str, float]]] = {
    "suite1a_order1": {
        "rouge_l_ar": ("ge", 44.44),
        "fwt": ("ge", 26.07),
        "bwt": ("ge", 1.76),
        "t_init": ("ge", 51.81),
        "t_unseen": ("ge", 38.39),
    },
    "suite2_final_aa": {"final_aa": ("ge", 84.37)},
    "suite3a_ser": {"ser_pct": ("le", 3.27)},
    "suite3a_bleu": {"bleu4": ("ge", 0.771)},
    "suite3b_intent": {"intent_acc": ("ge", 93.56)},
    "suite3b_jga": {"jga": ("ge", 43.36)},
    "suite3b_eer": {"eer": ("le", 4.46)},
    "suite3b_bleu": {"bleu": ("ge", 23.95)},
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_from_citb_final(data: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not data:
        return out
    # Common keys in final_metrics / aggregated exports
    for k in ("rouge_l_ar", "fwt", "bwt", "t_init", "t_unseen"):
        if k in data and data[k] is not None:
            out[k] = float(data[k])
    agg = data.get("aggregated") or data.get("paper_metrics") or {}
    if isinstance(agg, dict):
        seen = agg.get("seen_avg_rouge_l") or agg.get("rouge_l_mean")
        if seen is not None and "rouge_l_ar" not in out:
            # tracker uses percent scale
            v = float(seen)
            out["rouge_l_ar"] = v * 100.0 if v <= 1.5 else v
    extras = data.get("extra") or {}
    if isinstance(extras, dict):
        rl = extras.get("rouge_l_mean")
        if rl is not None and "rouge_l_ar" not in out:
            v = float(rl)
            out["rouge_l_ar"] = v * 100.0 if v <= 1.5 else v
    return out


def _check(name: str, metrics: Dict[str, float]) -> List[str]:
    fails: List[str] = []
    spec = TARGETS.get(name, {})
    for key, (op, target) in spec.items():
        if key not in metrics:
            fails.append(f"{name}:{key}=MISSING (need {op} {target})")
            continue
        val = metrics[key]
        ok = val >= target if op == "ge" else val <= target
        if not ok:
            fails.append(f"{name}:{key}={val} (need {op} {target})")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version-dir", default="v1_citb_kalman_drift")
    ap.add_argument("--run", default="citb_instrdialog_order1_seed1_ours_v1_strict")
    args = ap.parse_args()

    results_root = CAMPAIGN / args.version_dir / "results" / "runs" / args.run
    final_path = results_root / "final_metrics.json"
    metrics = _metric_from_citb_final(_load_json(final_path))

    report = {
        "run": args.run,
        "final_metrics_path": str(final_path),
        "extracted": metrics,
        "all_pass": False,
        "failures": _check("suite1a_order1", metrics),
    }
    report["all_pass"] = len(report["failures"]) == 0

    out_path = CAMPAIGN / "logs" / "sota_gap_check_latest.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
