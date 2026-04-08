from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _lookup_row(rows: Sequence[Dict[str, str]], *, benchmark: str, method_label: str) -> Dict[str, str]:
    for row in rows:
        if str(row.get("benchmark")) == benchmark and str(row.get("method_label")) == method_label:
            return dict(row)
    return {}


def _bar_colors(labels: Sequence[str], highlight: str = "Ours") -> List[str]:
    out: List[str] = []
    for label in labels:
        if highlight in label:
            out.append("#d55e00")
        elif "RouterOnly" in label:
            out.append("#8172b2")
        elif "Replay" in label:
            out.append("#4c72b0")
        else:
            out.append("#55a868")
    return out


def _annotate_bars(ax: plt.Axes, values: Sequence[float]) -> None:
    ymax = max(values) if values else 0.0
    pad = max(0.005, ymax * 0.03)
    for idx, value in enumerate(values):
        ax.text(idx, value + pad, f"{value:.3f}", ha="center", va="bottom", fontsize=8)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_instrdialog_main_tradeoffs(main_rows: Sequence[Dict[str, str]], out_path: Path) -> None:
    ordered_methods = [
        "Sequential",
        "Replay(10)",
        "Replay(50)",
        "PeriodicLatest",
        "BankNoRouter",
        "RouterOnly",
        "Ours",
    ]
    labels = ["Sequential", "Replay10", "Replay50", "Periodic", "BankNoRouter", "RouterOnly", "Ours"]
    metrics = [
        ("eval.seen_avg_score", "Seen Avg (higher is better)"),
        ("eval.forgetting", "Forgetting (lower is better)"),
        ("eval.token_f1_mean", "Token F1 (higher is better)"),
    ]
    rows = [_lookup_row(main_rows, benchmark="instrdialog", method_label=method) for method in ordered_methods]
    colors = _bar_colors(labels)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    x = np.arange(len(labels))
    for ax, (metric_key, title) in zip(axes, metrics):
        values = [_safe_float(row.get(metric_key)) for row in rows]
        ax.bar(x, values, color=colors)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        _annotate_bars(ax, values)
    fig.suptitle("InstrDialog Main Metrics vs Baselines", fontsize=14)
    _save(fig, out_path)


def _plot_routing_vs_performance(main_rows: Sequence[Dict[str, str]], ablation_rows: Sequence[Dict[str, str]], out_path: Path) -> None:
    points = [
        ("RouterOnly", _lookup_row(main_rows, benchmark="instrdialog", method_label="RouterOnly")),
        ("BankNoRouter", _lookup_row(main_rows, benchmark="instrdialog", method_label="BankNoRouter")),
        ("Ours(main=no_overlap)", _lookup_row(main_rows, benchmark="instrdialog", method_label="Ours")),
        ("OursFull", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursFull")),
        ("OursNoRouter", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursNoRouter")),
    ]

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for label, row in points:
        x = _safe_float(row.get("routing.oracle_agreement_rate"))
        y = _safe_float(row.get("eval.seen_avg_score"))
        size = 170 if "Ours" in label else 120
        color = "#d55e00" if "Ours(main" in label else "#4c72b0"
        if label == "RouterOnly":
            color = "#8172b2"
        elif label == "BankNoRouter":
            color = "#55a868"
        ax.scatter(x, y, s=size, color=color, alpha=0.9)
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(6, 6), fontsize=9)

    ax.set_title("Routing Quality vs Seen Avg")
    ax.set_xlabel("Oracle Agreement")
    ax.set_ylabel("Seen Avg Score")
    ax.grid(True, linestyle="--", alpha=0.3)
    _save(fig, out_path)


def _plot_drift_diagnostics(main_rows: Sequence[Dict[str, str]], ablation_rows: Sequence[Dict[str, str]], out_path: Path) -> None:
    rows = [
        ("BankNoRouter", _lookup_row(main_rows, benchmark="instrdialog", method_label="BankNoRouter")),
        ("Ours(main)", _lookup_row(main_rows, benchmark="instrdialog", method_label="Ours")),
        ("OursFull", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursFull")),
        ("OursNoRouter", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursNoRouter")),
    ]
    metrics = [
        ("drift.false_alarm_rate", "False Alarm Rate"),
        ("drift.miss_rate", "Miss Rate"),
        ("drift.detection_delay_mean", "Detection Delay Mean"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
    labels = [label for label, _ in rows]
    x = np.arange(len(labels))
    colors = _bar_colors(labels, highlight="Ours")
    for ax, (metric_key, title) in zip(axes, metrics):
        values = [_safe_float(row.get(metric_key)) for _, row in rows]
        ax.bar(x, values, color=colors)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        _annotate_bars(ax, values)
    fig.suptitle("Drift Diagnostics on InstrDialog", fontsize=14)
    _save(fig, out_path)


def _plot_ablation_heatmap(main_rows: Sequence[Dict[str, str]], ablation_rows: Sequence[Dict[str, str]], out_path: Path) -> None:
    rows = [
        ("Ours(main)", _lookup_row(main_rows, benchmark="instrdialog", method_label="Ours")),
        ("OursFull", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursFull")),
        ("OursNoRouter", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursNoRouter")),
        ("OursNoDrift", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursNoDrift")),
        ("OursNoBank", _lookup_row(ablation_rows, benchmark="instrdialog", method_label="OursNoBank")),
    ]
    metric_specs = [
        ("eval.seen_avg_score", "Seen Avg"),
        ("eval.forgetting", "Forgetting"),
        ("eval.token_f1_mean", "Token F1"),
        ("routing.oracle_agreement_rate", "Oracle Agr."),
    ]

    raw = np.array([[_safe_float(row.get(metric)) for metric, _ in metric_specs] for _, row in rows], dtype=float)
    norm = np.zeros_like(raw)
    for col in range(raw.shape[1]):
        col_vals = raw[:, col]
        vmax = float(np.max(col_vals))
        vmin = float(np.min(col_vals))
        if abs(vmax - vmin) < 1e-12:
            norm[:, col] = 0.5
        else:
            norm[:, col] = (col_vals - vmin) / (vmax - vmin)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    im = ax.imshow(norm, cmap="YlOrRd", aspect="auto", vmin=0.0, vmax=1.0)
    ax.set_xticks(np.arange(len(metric_specs)))
    ax.set_xticklabels([label for _, label in metric_specs])
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels([label for label, _ in rows])
    ax.set_title("Ours Family Ablations (color normalized per column)")

    for i in range(raw.shape[0]):
        for j in range(raw.shape[1]):
            ax.text(j, i, f"{raw[i, j]:.3f}", ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, out_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    results_dir = repo_root / "results"
    out_dir = results_dir / "analysis_figures"

    main_rows = _read_csv(results_dir / "tables" / "paper_main_results.csv")
    ablation_rows = _read_csv(results_dir / "tables" / "paper_ablation_results.csv")

    _plot_instrdialog_main_tradeoffs(main_rows, out_dir / "instrdialog_main_tradeoffs.png")
    _plot_routing_vs_performance(main_rows, ablation_rows, out_dir / "routing_vs_performance.png")
    _plot_drift_diagnostics(main_rows, ablation_rows, out_dir / "drift_diagnostics.png")
    _plot_ablation_heatmap(main_rows, ablation_rows, out_dir / "ours_ablation_heatmap.png")

    print(f"[run_v1_analysis] wrote charts to {out_dir}")


if __name__ == "__main__":
    main()
