# lora-run_v10 Strict Alignment Report

Updated: 2026-06-21 02:46 CST

Rule: no Method x Benchmark cell is strict unless the official source or paper setting, data processing, metric, runner, and full-run/equivalent evidence are all present. This report only downgrades or preserves status; it does not promote scaffold outputs to strict.

## Summary

- Matrix coverage: 40 / 40 cells.
- Strict-complete cells: 0.
- Near-strict / runner-ready diagnostic cells: 3.
- Blocked or still audit-needed cells: 37.
- Validation status: PASS

## Strict-complete

- None. No current cell has enough evidence to be marked strict.

## Near Strict / Useful Diagnostic Evidence

- Progressive Prompts / Seq-GLUE: `parser-implemented-paper-protocol-mismatch`. Evidence: Official source exists; preflight results/tables/seqglue_progressive_prompts_official_preflight.json records official T5 command plus matching README/T5 hparams plus new parser scripts/parse_progressive_prompts_results.py for official results_dict.npy to v10 JSON/CSV. Gap: Not strict: official runner uses HF loaders rather than the local train50/eval10 stream and the local 8-task order does not match published PP 15-task long orders from Appendix A.2.
- LFPT5 / InstrDialog++: `protocol-repaired-smoke-passed-needs-clean-rerun`. Evidence: Prior completed run remains diagnostic only: W&B run jvp9lun8 and diagnosis showed all exact-match metrics zero plus citbtask*/__ans__ leakage. The bridge now suppresses protocol tokens during generation and strips them after decoding; smoke results/tables/lfpt5_decoding_protocol_smoke.json passes. Gap: Need clean smoke/rerun because the repair is a protocol change and the prior run cannot be promoted; still need paper hparam citation for lr/kd_lamda/grad_accum/max_epoch and InstrDialog++ train/eval split.
- LFPT5 / Seq-GLUE: `user-stopped-partial-needs-clean-rerun-after-protocol-fix`. Evidence: User stopped fix3 at 2026-06-19T10:00:15+08:00; preserved partial metrics glue_sst2=1.0 glue_mrpc=0.8 glue_rte=0.6 glue_cola=0.5; LFPT5 protocol-token generation/decoding fix now smoke-passes in results/tables/lfpt5_decoding_protocol_smoke.json. Gap: Partial result only and earlier bridge had protocol leakage risk; protocol fix is not strict by itself and requires clean rerun plus paper hparam audit.

## Method-level Status

- Sequential LoRA: `local-adaptation-not-strict-paper-mismatch` x4; `stage2-seed227-ft-complete-replay-running-paper-mismatch` x1
- Replay LoRA: `local-adaptation-not-strict-paper-mismatch` x4; `stage2-seed227-replay-running-partial-paper-mismatch` x1
- O-LoRA: `completed-diagnostic-paper-benchmark-mismatch` x1; `official-source-needs-benchmark-bridge-and-paper-audit` x4
- LB-CL: `faithful-port-required` x5
- Progressive Prompts: `official-source-needs-bridge-and-paper-audit` x4; `parser-implemented-paper-protocol-mismatch` x1
- Continual-T0: `official-assets-partial-download-running-needs-assets` x1; `official-source-needs-bridge-and-paper-audit` x4
- LFPT5: `official-bridge-needs-paper-setting-audit` x3; `protocol-repaired-smoke-passed-needs-clean-rerun` x1; `user-stopped-partial-needs-clean-rerun-after-protocol-fix` x1
- Ours: `comparison-protocol-defined-not-strict-reproduction` x5

## Blocking Evidence

- Sequential LoRA / Replay LoRA: CITB official source, split/order files, LM-adapted T5-small asset, CPU-safe command planning, Replay(10/50) policy, and AR/FWT/BWT/FR metric helpers are present for InstrDialog. Stage-1 seed=50 full run is now running in `tmux` session `citb_stage1_seed50`; both cells remain non-strict until that checkpoint completes and the official Stage-2 full runs, metric parser, and paper comparison all pass.
- O-LoRA: official source, Seq-GLUE runner bridge, one official diagnostic full run, and paper mismatch audit are present; the local T5-small 8-segment bridge still does not match the published T5-large O-LoRA protocol or later Seq-GLUE-7 target.
- LB-CL: no dedicated official source was found after web searches; `results/tables/lb_cl_official_source_audit.json` records the evidence, so every tracked cell requires an audited faithful port before strict.
- Progressive Prompts / Continual-T0: PP now has an official command preflight and `results_dict.npy` parser, but the local 8-task bridge is not the published 15-task order; Continual-T0 has source plus CT0 tokenizer/config assets and an active full-checkpoint HF download, while Drive processed assets remain permission-blocked.
- LFPT5: task-token decoding leakage has a bridge-level protocol repair and smoke evidence, but prior runs remain diagnostic; clean one-segment smoke and full rerun are still required before any strict claim.
- TOD37: retired from the tracked benchmark matrix by user decision; it is no longer counted as a strict-alignment blocker.

## O-LoRA Seq-GLUE Bridge Check

- Manifest status: `completed`.
- Official entry: `external_baselines/o_lora/src/run_uie_lora.py`.
- Command includes official runner: `True`.
- Data bridge validation is enforced by `scripts/export_seqglue_to_olora.py --validate-only` and by the official runner dry-run path.
- Per-cell strict gates are also written to `results/tables/lora_run_v10_strict_alignment_evidence.json` for interruption-safe follow-up.

## Validation Errors

- None.
