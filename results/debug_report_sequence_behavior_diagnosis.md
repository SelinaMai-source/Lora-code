# Sequence behavior diagnosis report

## Framing

Observed pattern: **train loss → ~0**, **shifted teacher-forced token accuracy → ~1**, **train-mode answer token acc → ~1**, while **greedy open-loop exact match** stays low (e.g. ~1/8) and **prefix** metrics lag. We treat this as: **conditional distributions under teacher forcing are well fit**, but the **autoregressive rollout** (same weights, same prompts) does not land on the reference strings. This report does **not** re-litigate mask/shift correctness; it aggregates artifacts that localize *where* the open-loop trajectory diverges (first token, prefix, surface form, decode path, or deeper sequence mismatch).

- **run_id**: `baseline_alignment_overfit_bosfix_fulldiag`
- **experiment**: `citb_baseline_alignment_overfit`
- **artifacts**: `results/runs/baseline_alignment_overfit_bosfix_fulldiag/debug/overfit8`

Metrics legend: **baseline_eval_normalize_EM** uses `evaluate._normalize` (unchanged baseline). **strict_string_EM** is exact string equality. **diagnostic_norm_EM** uses `diagnostic_normalize` only.

## Q1 — What kind of failures dominate?

Compare `count_*` columns in the latest `step_XXXX_failure_summary.csv` with `raw_em_count` / `trimmed_em_count` / `normalized_em_count` to see whether errors are first-token, prefix drift, surface form, stop/over-gen, or content.

- Latest summary: `step_0020_failure_summary.csv`

| Metric | Value |
|---|---|
| count_content_wrong | 0 |
| count_empty_or_near_empty_output | 0 |
| count_extra_preamble | 2 |
| count_first_token_wrong | 5 |
| count_prefix_drift_1to5 | 1 |
| count_punctuation_only_mismatch | 0 |
| count_semantic_match_surface_mismatch | 1 |
| count_whitespace_or_newline_mismatch | 0 |
| count_wrong_stop_or_overgenerate | 0 |
| normalized_em_count | 2 |
| num_samples | 8 |
| raw_em_count | 2 |
| step | 20 |
| trimmed_em_count | 2 |

### Q1 answer (from latest failure summary)

Dominant tagged failure modes (top 3): `count_first_token_wrong`=5, `count_extra_preamble`=2, `count_prefix_drift_1to5`=1. Cross-check `raw_em_count` vs `trimmed_em_count` vs `normalized_em_count` for surface vs stop vs whitespace.


## Q2 — First-token margin: rank, prob gap, logit margin

- Logged rows: **40** (one per sample per eval step). **gold==greedy** rate: **0.300**.
- **Mean gold token rank** (0=greedy): **11337.05**; mean **logit margin** (greedy−gold): **7.9313**.
- Mean **prob(gold)** **0.2936**, mean **prob(greedy)** **0.6751** (gap **0.3814**).
- *Interpretation:* rank≈1–2 with small margin often means greedy is brittle though mass is near gold; large rank means the first answer token is not yet behaviorally locked under this prompt format.

### Q2 answer

_Aggregate over 40 rows: mean rank 11337.05, mean greedy−gold logit margin 7.9313, mean prob gap (greedy−gold) 0.3814._


## Q3 — Prefix rollouts: does forcing 1/3/5 gold tokens fix generation?

- **prefix_len=0** (last eval step in log): strict_string_EM=3/8, diagnostic_norm_EM=3/8, prefix1=0.5, token_f1_mean=0.48415843728343727, lcs_overlap_mean=0.5904179495951648
- **prefix_len=1** (last eval step in log): strict_string_EM=1/8, diagnostic_norm_EM=1/8, prefix1=0.75, token_f1_mean=0.42906434088210305, lcs_overlap_mean=0.656744561016713
- **prefix_len=3** (last eval step in log): strict_string_EM=3/8, diagnostic_norm_EM=3/8, prefix1=1.0, token_f1_mean=0.5030918839269458, lcs_overlap_mean=0.7993428555137416
- **prefix_len=5** (last eval step in log): strict_string_EM=3/8, diagnostic_norm_EM=3/8, prefix1=1.0, token_f1_mean=0.5181397699761798, lcs_overlap_mean=0.802507412475767, clamped_short_gold=1
- *Interpretation:* a large jump from prefix_len 0→1 implicates **first-token / early-step** instability; little gain through 5 suggests **deeper** trajectory mismatch beyond the first few tokens.

### Q3 answer

_See table above: compare normalized_EM and prefix acc across prefix_len 0 vs 1 vs 3 vs 5._


## Q4 — Decode ablation: does beam beat greedy?

- **greedy**: strict_string_EM=2/8, trimmed=2/8, diagnostic_norm=2/8, prefix1=0.375
- **beam2**: strict_string_EM=2/8, trimmed=2/8, diagnostic_norm=2/8, prefix1=0.375
- **beam4**: strict_string_EM=3/8, trimmed=3/8, diagnostic_norm=3/8, prefix1=0.5
- *Interpretation:* if beam materially raises EM / F1, the reference string may sit in the distribution but **greedy path** is unstable. If beam barely helps, the model may not assign enough mass to the reference continuation under this decode setup.

### Q4 answer

_Compare greedy vs beam2 vs beam4 rows above on diagnostic_norm and prefix1._


## Q5 — Overfit ladder: when does behavior break (1/2/4/8)?

- **n=1** (20 steps): final_train_loss=0.0001902572112157941, tf_shifted_acc=0.3612598339160839, raw_EM=0/8, diagnostic_norm_EM=0/8, baseline_eval_norm_EM=0/8, p1/p3/p5=0.0/0.0/0.0, F1=0.12438151788676377, LCS=0.18662819691300703
- **n=2** (20 steps): final_train_loss=0.00019473191787255928, tf_shifted_acc=0.41513694638694637, raw_EM=1/8, diagnostic_norm_EM=1/8, baseline_eval_norm_EM=1/8, p1/p3/p5=0.125/0.125/0.125, F1=0.2340185795197257, LCS=0.333972308655853
- **n=4** (20 steps): final_train_loss=0.0003238254284951836, tf_shifted_acc=0.5704399766899767, raw_EM=0/8, diagnostic_norm_EM=0/8, baseline_eval_norm_EM=0/8, p1/p3/p5=0.0/0.0/0.0, F1=0.3279499641331745, LCS=0.39063870606592127
- **n=8** (20 steps): final_train_loss=0.0004212941821606364, tf_shifted_acc=1.0, raw_EM=2/8, diagnostic_norm_EM=2/8, baseline_eval_norm_EM=2/8, p1/p3/p5=0.5/0.5/0.375, F1=0.49899695526723153, LCS=0.7015551944349413

### Q5 answer

_raw EM fails already at n=1 (fundamental decode/alignment issue)_


## Q6 — Primary bottleneck (heuristic → one label)

Allowed labels: decode-path instability; first-token margin too weak; reference normalization mismatch; stop-condition / output-format mismatch; deeper sequence-level behavior mismatch not solved by token-level fitting.


### Q6 — Direct conclusion (single primary bottleneck)

**first-token margin too weak**
