# CCIR SOTA Research Notes

**Updated**: 2026-06-24

## Blocking issues (resolved in v1.1 patch)

1. **overlap_loss CUDA/CPU crash** when drift spawns branch `b1`: `HFSeq2SeqLMBackbone.get_activations_tensor(with_grad=False)` returns CPU tensors; active branch stays on CUDA → fixed via device alignment in `overlap_loss.py`.
2. **Missing CITB AR aggregation** in strict runner — wired `ccfa_metrics.write_ccfa_postprocess_outputs` into `train.py`.

## Current campaign status

| Run | Outcome | Notes |
|-----|---------|-------|
| smoke_v1 | ✅ | seg0 OK |
| order1 v1 | ❌ seg2 crash | pre-fix overlap bug |
| order2 v1 | ❌ seg5 crash | same bug at first drift spawn |
| order3 v1 | ❌ interrupted | pre-fix; stopped after fix landed |
| order1 v1 rerun | 🔄 | post-fix, wandb `ours-sota-campaign` |

## CCIR novelty (incremental)

Task-free continual LoRA with **Chat-aware Confidence-Informed Routing**: combine prototype margin gating, NLL arbitration on uncertain routes, and matched-KL orthogonal regularization across bank branches — without task boundaries.

Distinct from: Kalman weight tracking (DeepMind OCL), supervised HMM task boundaries, uniform replay baselines.

## Gap targets (Suite 1A)

See [SOTA_GAP_TRACKER.md](./SOTA_GAP_TRACKER.md). Primary metric: ROUGE-L AR ≥ 44.44 (+10% vs baseline 40.4).

## Next experiments

1. Complete v1 order1–3 strict with device fix
2. A/B v1 vs v1.1 CCIR on order1 seed1
3. Suite 2 T5-Large with optional `spectral_replay`
