# lora-run_v10 Master Plan

Updated: 2026-06-18 05:20 CST

## Scope And Guardrails

- Goal: single-seed (`123`) reproduction of LoRA continual-learning baselines in the closest available published-paper setting, not the current unified Llama-LoRA scaffold.
- W&B: every new/restarted run must use project `lora-run_v10`; group names should also start with `lora-run_v10`.
- Execution: full runs must be launched in tmux.
- Conflict boundary: do not edit `results/tables/published_setting_run_v2_gap_manifest.csv`, `results/tables/published_setting_run_v2_gap_status.csv`, or partial/checkpoint archives owned by the focused blocked-unlock worker.
- Reporting rule: scaffold outputs can be used for debugging/reference only. They must not be reported as strict paper-aligned results.

## Local Smoke Result

Command run locally without external downloads:

```bash
python scripts/smoke_published_setting_pipeline.py --skip-external
```

Result: passed. All configs under `configs/paper/published_setting/` parse and load local processed streams, including Seq-GLUE 8 segments, TRACE 8 segments, MultiWOZ 5 domains, InstrDialog 19 segments, and InstrDialog++ 38 segments. The smoke also revalidated the existing published InstrDialog/InstrDialog++ CSV final metrics against the expected seed-123 table. This is only a config/data-load smoke; it does not upgrade scaffold methods to strict paper-aligned results.

## Method x Benchmark Executability Matrix

| Method | InstrDialog | InstrDialog++ | TRACE | MultiWOZ NLG | Seq-GLUE | Strict paper-aligned status |
| --- | --- | --- | --- | --- | --- | --- |
| Sequential LoRA | Config/data ready; v10-compatible rerun possible | Config/data ready; prior partial now completed in reference tables | Config/data ready | Config/data ready | Config/data ready | Basic baseline in unified LoRA pipe; usable as a local baseline, but not a method-paper official reproduction. |
| Replay LoRA | Config/data ready; queued/reference outputs exist | Config/data ready | Config/data ready | Config/data ready | Config/data ready | Basic replay baseline in unified LoRA pipe; local comparison only unless paper-specific replay protocol is established. |
| O-LoRA | Config/data ready; prior reference output exists | Config/data ready; prior reference output exists | Config/data ready | Config/data ready | Config/data ready | Scaffold in unified pipe. Strict O-LoRA requires official implementation/settings; do not call current outputs paper-aligned. |
| LB-CL | Config/data ready; prior reference output exists | Config/data ready; prior reference output exists | Config/data ready | Config/data ready | Config/data ready | Scaffold in unified pipe. Strict LB-CL requires official projection/triplet pipeline; do not call current outputs paper-aligned. |
| Progressive Prompts | Config/data ready; prior reference output exists | Config/data ready; prior reference output exists | Config/data ready | Config/data ready | Config/data ready | Scaffold in unified pipe. Strict PP requires soft-prompt implementation and paper routing/setup. |
| Continual-T0 | Config/data ready; prior reference output exists | Config/data ready; prior reference output exists | Config/data ready | Config/data ready | Config/data ready | Scaffold in unified pipe. Strict C-T0 requires T0/T5 mixture, checkpoint, and official rehearsal setup. |
| LFPT5 | External T5 runner config/data ready | External T5 runner config/data ready; blocked-unlock queue owns restart | External T5 runner config/data ready | External T5 runner config/data ready, metric caveats remain | Running now in v10 tmux | Best current strict candidate because it uses separate LFPT5/T5 prompt-tuning path and LM-adapted T5-large checkpoint. |
| Ours | Completed/reference outputs for CITB | Completed/reference outputs for CITB | Config/data ready; TRACE delta metrics need audit | Config/data ready; slot error missing | Config/data ready; prior v10 status shows weak gap | Project method, not a baseline-paper reproduction; can be run for our table but must be separated from official baseline claims. |

Legend: `Config/data ready` means local smoke can parse YAML and load processed data with no network. `Reference output` means prior run artifacts exist, often from `published_setting_run_v2`; those are useful for audit but not automatically v10-compliant because W&B project/group may differ. TOD37 is retired and no longer part of this matrix.

## Current First-Batch Run

| Field | Value |
| --- | --- |
| tmux session | `lora_run_v10_queue` |
| run | `lora_run_v10_seqglue_lfpt5_s123` |
| method | LFPT5 |
| benchmark | Seq-GLUE 8-task stream |
| config | `configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml` |
| runner | `scripts/run_lfpt5_published_setting.py` -> `external_baselines/lfpt5/citb_bridge/run_continual.py` |
| W&B | project `lora-run_v10`, group `lora-run_v10_seqglue_lfpt5` |
| backbone/checkpoint | LM-adapted T5-large, `assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin` |
| seed | `123` |
| budget | 8 segments, train50/eval10, `max_epoch=4`, prompt number 300, batch size 2 |
| metrics | `seen_avg_score`, `seen_avg_task_aware_score`, `token_f1_mean`, `forgetting` |
| status | running; reached Seq-GLUE segment 2 by 05:13 CST |

This is the first strict candidate because LFPT5 uses its separate T5 prompt-tuning path and an LM-adapted T5-large checkpoint. It is materially closer to the LFPT5 paper protocol than the unified Llama-LoRA scaffold.

Smoke/config checks already satisfied for this run:

- Config points to `seqglue_cl_tasks_train50_eval10.json` with `max_segments: -1`.
- Wrapper exported 8 segment directories and wrote `run_manifest.json`.
- Checkpoint is present and `checkpoint_ready: true`.
- W&B online run is active in project `lora-run_v10`.

## Target Paper/Table Matrix

| Priority | Target | Method | Benchmark | Published-setting requirement | Current local status | Action |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | LFPT5 ICLR 2022 lifelong few-shot prompt tuning | LFPT5 | Seq-GLUE | LM-adapted T5-large, prompt tuning, sequential task stream, few-shot train/eval, paper-aligned forgetting/accuracy-style metrics | Running in `lora_run_v10_queue` | Let full run finish, then compare final table against prior LFPT5 Seq-GLUE/reference outputs and inspect large gaps before expanding |
| P1 | LFPT5 ICLR 2022 | LFPT5 | InstrDialog++ | Same LFPT5 external runner; CITB stream export | Paused/blocked in v2 gap status because v10 owns GPU | Restart only after P0 finishes, using project/group `lora-run_v10`; do not modify gap worker files |
| P2 | LFPT5 ICLR 2022 | LFPT5 | InstrDialog, TRACE, MultiWOZ NLG | Same LFPT5 external runner; benchmark-specific metric caveats | Completed earlier under mixed project/status tables; needs v10-consistent audit or rerun decision | Treat as reference until rerun/audited under `lora-run_v10` |
| P3 | O-LoRA EMNLP Findings 2023 | O-LoRA | TRACE or Seq-GLUE | Official O-LoRA environment, official task configs, T5/LLaMA weights as specified by paper | Local unified configs are scaffold/orthogonal-hook only | Blocked for strict claim until official environment/configs are launched |
| P4 | LB-CL NeurIPS 2024 | LB-CL | Seq-GLUE | Official LB-CL triplet sensitivity/projection pipeline and paper task order/metrics | Local unified config is scaffold with SVD/projection hook | Blocked for strict claim until official pipeline is implemented or official code is available |
| P5 | Progressive Prompts ICLR 2023 | Progressive Prompts | TRACE or Seq-GLUE | Soft prompt modules, prompt concatenation, non-oracle routing, T5/BERT paper setup | Local unified config is prompt schedule scaffold | Blocked for strict claim until official prompt implementation/env is runnable |
| P6 | Continual-T0 EMNLP 2022 | Continual-T0 | Seq-GLUE/T0-style stream | T0/T5 checkpoint, official mixture, 1% rehearsal | Local unified config is instruction-replay scaffold | Blocked for strict claim until T0 environment/data/checkpoint are prepared |
| P7 | AdapterCL/ToDCL / ARPER dialogue NLG | Sequential/Replay-style dialogue baselines | MultiWOZ NLG | Official dialogue NLG env and metrics including slot error where required | Source exists; MultiWOZ local metrics need audit | Blocked for strict claim until env/metric alignment is complete |

## Command Templates

Current active tmux queue:

```bash
tmux new-session -d -s lora_run_v10_queue \
  'cd /root/autodl-tmp/Lora-code && WANDB_PROJECT=lora-run_v10 WANDB_MODE=online bash scripts/run_lora_run_v10_queue.sh'
```

Direct smoke/config check template for LFPT5 candidates:

```bash
cd /root/autodl-tmp/Lora-code
WANDB_PROJECT=lora-run_v10 WANDB_MODE=online \
python scripts/run_lfpt5_published_setting.py \
  --config configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml --dry-run
```

Direct full-run template, only when no training process owns the GPU:

```bash
cd /root/autodl-tmp/Lora-code
WANDB_PROJECT=lora-run_v10 WANDB_GROUP=lora-run_v10_seqglue_lfpt5 WANDB_MODE=online \
python scripts/run_lfpt5_published_setting.py \
  --config configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml
```

## Validation After Completion

1. Confirm `results/runs/lora_run_v10_seqglue_lfpt5_s123/final_metrics.json` exists.
2. Confirm `results/tables/lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv` has 8 rows.
3. Compare final `seen_avg_score`, `seen_avg_task_aware_score`, `token_f1_mean`, and `forgetting` against the published-setting/reference LFPT5 Seq-GLUE output.
4. If the gap is large, inspect task order/splits, prompt length, LM-adapted checkpoint loading, generated replay memory, metric normalization, and W&B logs before launching the next full run.
5. Only after LFPT5 P0 is stable, choose the next v10 paper-aligned target. Do not fill the master table with scaffold results.

## Known Blockers

- O-LoRA, LB-CL, Progressive Prompts, and Continual-T0 local unified-entry results are not strict published-paper reproductions.
- MultiWOZ NLG local published-setting notes still lack slot error; BLEU/ROUGE are implemented but may not fully match dialogue NLG papers.
- TOD37 is retired from the active benchmark matrix and no longer blocks strict comparison.
- TRACE v2 reference rows now have outputs, but strict TRACE paper deltas and official O-LoRA/PP settings still need audit before being called paper-aligned.
