# CCIR v1.1 — Incremental Proposal

**Parent**: `v1_citb_kalman_drift`  
**Archive**: `experiments/sota_campaign/v1_1_ccir_router_kl/`  
**Runtime**: `/root/autodl-tmp/Lora-code/core/` (live code; version dir holds snapshot + configs)

## Delta from v1

| Knob | Config path | Mechanism |
|------|-------------|-----------|
| Device-safe anti-overlap | code fix | Align branch activations + LoRA vectors on model device before overlap loss |
| CCIR routing bundle | `router.use_chat_aware_routing: true` | Enables existing hooks: `nll_arbitration`, `margin_gated_soft_routing`, `prototype_calibration` |
| Matched KL bank reg | `orthogonal_regularization.kl_mode: matched`, `kl_bank_lambda: 0.05` | Uses `information_bottleneck` weight similarity scaled by lambda |
| CITB paper metrics | `core/ccfa_metrics.py` | Writes `ccfa_postprocess/summary.json` + top-level `rouge_l_ar`, `fwt`, `bwt` in `final_metrics.json` |
| Optional replay (Suite 2) | `spectral_replay.enabled: true` | Existing `SpectralSparseReplayGate` — enable only in Suite 2 configs when queued |

## Config template

See `v1_1_ccir_router_kl/configs/citb_instrdialog_order1_seed1_ours_v1_1_strict.yaml`.

## Validation queue

1. v1 strict rerun (device fix only) — `citb_instrdialog_order1_seed1_ours_v1_strict`
2. v1.1 CCIR ablation — `citb_instrdialog_order1_seed1_ours_v1_1_strict`
3. Suite 2 with `spectral_replay` when configs land in `suite23_queue.txt`
