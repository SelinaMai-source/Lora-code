# RP Alignment Progress Report

## Behavior Gate

- Overfit exact match improved from `1/8` to `3/8` after removing duplicated BOS in generation-time prompt tokenization.
- First-token failures dropped from `6` to `4`; extra-preamble failures changed from `1` to `2`.
- Remaining failures are still dominated by first-token misses and over-generation on a few samples, so the BOS fix removes a pipeline bug but does not fully solve exposure bias.

## Baseline Recovery

- Wrote baseline comparison table: `results/tables/baseline_bosfix_comparison.csv`
- Wrote baseline quality figure: `results/figures/baseline_bosfix_quality.png`
- Recovery mini run `baseline_recovery_mini_seq` reached `train_answer_acc=0.745`, `prefix1=0.300`, `prefix3=0.100`, `prefix5=0.050`, while `current_score` remained `0.000`.
- Among smoke baselines, `router_smoke` had the highest `token_f1=0.249` with `prefix1=0.300`, but all smoke runs still stayed at `current_score=0.0`.

## Ours Smoke Ablation

- Wrote ablation table: `results/tables/ours_smoke_bosfix_ablation_summary.csv`
- Wrote ablation figure: `results/figures/ours_smoke_bosfix_ablation.png`
- Full stack `ours_full` produced `bank.num_branches=3`, `routing.num_routed=10`, `router.num_updates=0`, and `drift.ema=1.0000`.
- Best ablation by token F1 was `ours_no_router` with `token_f1=0.236` and `prefix1=0.300`.

## Artifacts

- Overfit comparison table: `results/tables/overfit_bosfix_comparison.csv`
- Overfit progress figure: `results/figures/overfit_bosfix_progress.png`
- Error analysis table: `results/tables/overfit_bosfix_error_examples.csv`
