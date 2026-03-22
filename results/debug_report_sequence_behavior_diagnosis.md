# Sequence behavior diagnosis report

## Framing

Observed pattern: **train loss → ~0**, **shifted teacher-forced token accuracy → ~1**, **train-mode answer token acc → ~1**, while **greedy open-loop exact match** stays low (e.g. ~1/8) and **prefix** metrics lag. We treat this as: **conditional distributions under teacher forcing are well fit**, but the **autoregressive rollout** (same weights, same prompts) does not land on the reference strings. This report does **not** re-litigate mask/shift correctness; it aggregates artifacts that localize *where* the open-loop trajectory diverges (first token, prefix, surface form, decode path, or deeper sequence mismatch).

- **run_id**: `baseline_alignment_overfit`
- **experiment**: `citb_baseline_alignment_overfit`
- **artifacts**: `results/runs/baseline_alignment_overfit/debug/overfit8`

Metrics legend: **baseline_eval_normalize_EM** uses `evaluate._normalize` (unchanged baseline). **strict_string_EM** is exact string equality. **diagnostic_norm_EM** uses `diagnostic_normalize` only.

## Q1 — What kind of failures dominate?

Compare `count_*` columns in the latest `step_XXXX_failure_summary.csv` with `raw_em_count` / `trimmed_em_count` / `normalized_em_count` to see whether errors are first-token, prefix drift, surface form, stop/over-gen, or content.

- Latest summary: `step_0020_failure_summary.csv`

| Metric | Value |
|---|---|
| count_content_wrong | 0 |
| count_empty_or_near_empty_output | 0 |
| count_extra_preamble | 1 |
| count_first_token_wrong | 6 |
| count_prefix_drift_1to5 | 1 |
| count_punctuation_only_mismatch | 0 |
| count_semantic_match_surface_mismatch | 1 |
| count_whitespace_or_newline_mismatch | 0 |
| count_wrong_stop_or_overgenerate | 0 |
| normalized_em_count | 1 |
| num_samples | 8 |
| raw_em_count | 1 |
| step | 20 |
| trimmed_em_count | 1 |

### Q1 answer (from latest failure summary)

Dominant tagged failure modes (top 3): `count_first_token_wrong`=6, `count_prefix_drift_1to5`=1, `count_semantic_match_surface_mismatch`=1. Cross-check `raw_em_count` vs `trimmed_em_count` vs `normalized_em_count` for surface vs stop vs whitespace.


## Q2 — First-token margin: rank, prob gap, logit margin

- Logged rows: **40** (one per sample per eval step). **gold==greedy** rate: **0.200**.
- **Mean gold token rank** (0=greedy): **13725.02**; mean **logit margin** (greedy−gold): **9.2485**.
- Mean **prob(gold)** **0.1915**, mean **prob(greedy)** **0.7116** (gap **0.5201**).
- *Interpretation:* rank≈1–2 with small margin often means greedy is brittle though mass is near gold; large rank means the first answer token is not yet behaviorally locked under this prompt format.

### Q2 answer

_Aggregate over 40 rows: mean rank 13725.02, mean greedy−gold logit margin 9.2485, mean prob gap (greedy−gold) 0.5201._


## Q3 — Prefix rollouts: does forcing 1/3/5 gold tokens fix generation?

_No prefix_rollout_summary.csv._

## Q4 — Decode ablation: does beam beat greedy?

- **greedy**: strict_string_EM=1/8, trimmed=1/8, diagnostic_norm=1/8, prefix1=0.25
- **beam2**: strict_string_EM=1/8, trimmed=1/8, diagnostic_norm=1/8, prefix1=0.25
- **beam4**: strict_string_EM=1/8, trimmed=1/8, diagnostic_norm=1/8, prefix1=0.25
- *Interpretation:* if beam materially raises EM / F1, the reference string may sit in the distribution but **greedy path** is unstable. If beam barely helps, the model may not assign enough mass to the reference continuation under this decode setup.

### Q4 answer

_Compare greedy vs beam2 vs beam4 rows above on diagnostic_norm and prefix1._


## Q5 — Overfit ladder: when does behavior break (1/2/4/8)?

_No overfit_ladder.csv._

### Q5 answer

_unknown (missing CSV)_


## Q6 — Primary bottleneck (heuristic → one label)

Allowed labels: decode-path instability; first-token margin too weak; reference normalization mismatch; stop-condition / output-format mismatch; deeper sequence-level behavior mismatch not solved by token-level fitting.


### Q6 — Direct conclusion (single primary bottleneck)

**deeper sequence-level behavior mismatch not solved by token-level fitting**
