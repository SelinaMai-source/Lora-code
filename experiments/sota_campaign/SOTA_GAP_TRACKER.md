# SOTA Gap Tracker — Ours vs +10% CL Baseline

**Updated**: 2026-06-24 06:10 CST  
**Rule**: higher-is-better → target = baseline × 1.10; lower-is-better → target = baseline × 0.90 (BWT: +10% toward positive).

## Executive Summary

| Suite | Status | Metrics tracked | Pass | Fail | Largest gap | Smallest gap |
|-------|--------|-----------------|------|------|-------------|--------------|
| 1A InstrDialog | **blocked → fix landed** | 5 | 0 | 5 | **AR** (~97%) | **BWT** (~102% rel.) |
| 1B InstrDialog++ | not started | 5 | 0 | 5 | all missing | — |
| 2 T5-Large PEFT CL | config only | 1 | 0 | 1 | **Final AA** (100% missing) | — |
| 3A ARPER 7-intent | stale | 2 | 0 | 2 | all missing | — |
| 3B ToDCL Modular NLG | not started | 4 | 0 | 4 | all missing | — |

**Campaign priority**: Fix Suite 1 CITB eval/training alignment (blocking bug), then re-run strict CITB before Suite 2/3.

---

## Suite 1A — CITB InstrDialog (19 tasks)

**Best Ours (strict)**: `citb_instrdialog_order1_seed1_ours_strict` — completed 19/19 segments (2026-06-23).  
**Note**: Scores reflect **misaligned prompt format** (Llama-style constraint text on T5); v1 fixes this.

| Metric | Dir | SOTA target | Current best | Gap | Pass |
|--------|-----|-------------|--------------|-----|------|
| ROUGE-L AR | ↑ | ≥ 44.44 | **1.32** (seen_avg×100 @ seg18) | −97.0% | ❌ |
| FWT | ↑ | ≥ 26.07 | *null / not aggregated* | — | ❌ |
| BWT | ↑ | ≥ 1.76 | **−4.17** (est. from forgetting) | — | ❌ |
| T_init | ↑ | ≥ 51.81 | *not measured* | — | ❌ |
| T_unseen | ↑ | ≥ 38.39 | *not measured* | — | ❌ |

**Running**: none (order1–3 v1 crashed pre-fix; post-fix rerun queued — see `launch_order1_v1_rerun.sh`).

**Post-fix**: `final_metrics.json` now includes `rouge_l_ar`, `fwt`, `bwt` via `ccfa_postprocess` when runs complete.

**Non-comparable reference** (Llama published_setting): seen_avg 0.3307 — different backbone/metrics.

---

## Suite 1B — CITB InstrDialog++ (38 tasks)

| Metric | Dir | SOTA target | Current best | Gap | Pass |
|--------|-----|-------------|--------------|-----|------|
| ROUGE-L AR | ↑ | ≥ 47.41 | — | — | ❌ |
| FWT | ↑ | ≥ 32.78 | — | — | ❌ |
| BWT | ↑ | ≥ −2.52 | — | — | ❌ |
| T_init | ↑ | ≥ 48.40 | — | — | ❌ |
| T_unseen | ↑ | ≥ 39.49 | — | — | ❌ |

---

## Suite 2 — T5-Large Standard PEFT CL (5 tasks, 3-order avg)

| Metric | Dir | SOTA target | Current best | Gap | Pass |
|--------|-----|-------------|--------------|-----|------|
| Final AA | ↑ | ≥ **84.37** | — (stale config) | — | ❌ |

> SOTA 84.37 exceeds MTL upper bound 80.0 — document when reporting.

---

## Suite 3A — ARPER 7-intent (Ω_all)

| Metric | Dir | SOTA target | Current best | Gap | Pass |
|--------|-----|-------------|--------------|-----|------|
| SER% | ↓ | ≤ 3.27 | — | — | ❌ |
| BLEU-4 | ↑ | ≥ 0.771 | — | — | ❌ |

---

## Suite 3B — ToDCL Modular NLG (37 domains)

| Metric | Dir | SOTA target | Current best | Gap | Pass |
|--------|-----|-------------|--------------|-----|------|
| Intent Acc | ↑ | ≥ 93.56 | — | — | ❌ |
| JGA | ↑ | ≥ 43.36 | — | — | ❌ |
| EER | ↓ | ≤ 4.46 | — | — | ❌ |
| BLEU | ↑ | ≥ 23.95 | — | — | ❌ |

---

## Gap ranking (actionable)

1. **Largest gap**: Suite 1 AR (pipeline bug — not true algorithm gap until v1 validated)
2. **Smallest gap among measured**: Suite 1 BWT (still far from target; sign wrong)
3. **Next bottleneck after fix**: T_init / T_unseen retention eval not wired in strict runner
