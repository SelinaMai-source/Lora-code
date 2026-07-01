# lora-run_v10 Strict Paper-Setting Checklist

Updated: 2026-06-19 23:55 CST

Execution rule: no new full training run may be launched for a Method x Benchmark cell until this checklist has a complete published-paper setting audit for that exact cell and the tracker row is moved out of `needs-paper-setting-audit` or `blocked-*`. Existing runs are not killed by this document; if an existing run predates the completed checklist it must be labelled `running-needs-setting-verification`.

Benchmark order for each method: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE. TOD37 has been retired from the tracked benchmark matrix by user decision and is no longer counted as a strict-alignment blocker.

## 2026-06-19 Strict-Alignment Push

- O-LoRA / Seq-GLUE now has an executable strict preflight audit at `scripts/audit_olora_seqglue_strict_preflight.py`. It validates bridge paths, official dry-run command manifest, segment order, and label sets, and writes `results/tables/olora_seqglue_strict_preflight_audit.json`. Status is `strict-preflight-ready-needs-full-run-and-paper-audit`, not strict-complete.
- LFPT5 / InstrDialog++ now has a protocol diagnosis script at `scripts/diagnose_lfpt5_protocol.py`. The completed run is confirmed non-strict: predictions leak `citbtask*` and `__ans__`, exact-match is all zero, and token F1 is near zero, so the next work is decoding/protocol repair before rerun.
- Sequential LoRA / Replay LoRA now have CITB T5 strict skeleton configs and a CPU preflight runner: `configs/paper/lora_run_v10/instrdialog__citb_t5_sequential__s123.yaml`, `configs/paper/lora_run_v10/instrdialog__citb_t5_replay50__s123.yaml`, and `scripts/run_citb_t5_strict_baseline.py`. They explicitly replace the non-strict local Llama LoRA adaptation path, but remain blocked on T5 modules, official splits, T5-small assets, and AR/FWT/BWT/FR metrics.
- Progressive Prompts / Seq-GLUE now has official-source bridge skeleton config `configs/paper/lora_run_v10/seqglue__progressive_prompts_official__s123.yaml` plus preflight command generation in `scripts/preflight_official_prompt_baselines.py`. It maps the 8 Seq-GLUE segments to official T5 task names, but still needs result parsing and paper task-order/hparam audit.
- Continual-T0 / Seq-GLUE now has config `configs/paper/lora_run_v10/seqglue__continual_t0_official__s123.yaml` and the same preflight script records the official asset blockers. It remains `strict-runner-skeleton-needs-official-assets`.
- TOD37 is retired from this reproduction matrix. Existing blocker manifests may remain as archival notes, but no TOD37 cell is counted, queued, or required for strict alignment.

## Recent LFPT5 InstrDialog++ Completion / Non-Strict

- Cell: LFPT5 / InstrDialog++ / seed 123.
- Process evidence: the earlier tmux session `lora_run_v10_instrdialogpp_lfpt5_clean` is no longer listed, CUDA 0 is idle, and `results/runs/published_instrdialogpp_lfpt5_s123/run_manifest.json` records `status: completed`.
- Config/runtime evidence: `configs/paper/published_setting/instrdialogpp__lfpt5__s123.yaml` records LM-adapted T5-large, prompt number 300, batch size 2, max length 128, InstrDialog++ stream `citb_cl_38_random_tasks_train50_eval10.json`, seed 123, and W&B project/group `lora-run_v10`. The manifest records 38 segments and bridge command `--max-epoch 4 --cuda 0`.
- Result evidence: `results/runs/published_instrdialogpp_lfpt5_s123/final_metrics.json` and the segment table cover all 38 segments, but every observed `eval.current_score`, `eval.seen_avg_score`, `eval.current_task_aware_score`, and `eval.seen_avg_task_aware_score` is 0.0; final token F1 is only 0.0020266388509749445.
- Missing audit / non-aligned signal: the config and active command still do not prove that LFPT5 default `lr=5e-5`, `kd_lamda=0.05`, `gradient_accumulation_steps=1`, `max_epoch=4`, exact-match/token-F1 scoring, and the InstrDialog++ train50/eval10 protocol match the LFPT5 published-paper setting. The all-zero exact-match result is an obvious suspicious/non-aligned signal.
- Recommendation: preserve the output as a diagnostic completed run only. Do not use it as `strict-complete`; if the user wants strict LFPT5 / InstrDialog++ later, audit the LFPT5 paper protocol first and rerun with corrected settings.

## Sequential LoRA

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | External source found: CITB: A Benchmark for Continual Instruction Tuning (EMNLP Findings 2023 / OpenReview) defines InstrDialog and InstrDialog++ and reports sequential fine-tuning baselines (`FT-init`, `FT-no-init`). It does not define the local Llama Sequential LoRA setting as a paper baseline. | Benchmark source found; Sequential LoRA still not paper-verified |
| Official implementation path | Current path is unified local config plus `core/train.py`; example config `configs/paper/published_setting/instrdialog__sequential_lora__s123.yaml`. `baselines/basic_baselines/sequential_lora/method.py` confirms a single default adapter trained segment by segment with no bank/router/replay. No dedicated official Sequential LoRA source exists under `external_baselines`. | Not official-paper verified |
| Backbone | Config evidence: Llama-3.1-8B-Instruct at `assets/pretrained/meta-llama/Llama-3.1-8B-Instruct`. CITB paper evidence: LM-adapted T5-small initialized from `google/t5-small-lm-adapt` and initial instruction-tuned on 100 non-overlapping tasks. | Mismatch / blocker |
| Adapter/prompt params | Config evidence: LoRA r16 alpha32 dropout0.05 target `q_proj`/`v_proj`. CITB paper baselines are full fine-tuning (`Tun=1`) or AdapterCL; no LoRA rank/alpha/dropout is specified for FT-init. | Mismatch / blocker |
| Optimizer/lr/batch/epochs/steps | Config evidence: lr 2e-4, batch 2, 1 epoch per segment, weight decay 0, grad clip 1.0. Code evidence: `core/models/lora_wrapper.py` uses AdamW over LoRA parameters and updates the optimizer LR from `fit_batch`; no scheduler or gradient clipping is applied in `step_adapter()` despite config fields. | Needs paper match |
| Task order | Local processed streams exist for InstrDialog, InstrDialog++, TRACE, MultiWOZ NLG, Seq-GLUE. CITB says the experiments randomly permute task streams, use three random seeds, refer to this as task order 1, and list selected tasks/orders in appendix tables; the local stream order has not been checked against those appendix orders. | Needs task-order audit |
| Split/data path | Example local data path `data/processed/citb_cl_dialogue_tasks_train50_eval10.json`. CITB paper evidence: InstrDialog uses 500/50/100 train/dev/test per task; InstrDialog++ uses 100/50/100. Local config is train50/eval10 and lacks a dev split. | Mismatch / blocker |
| Metrics/eval protocol | `core/evaluate.py` evaluates all seen segments after each segment and logs exact-match current/seen scores, task-aware scores, forgetting, token F1, LCS, ROUGE-L, BLEU, and slot error when slots are present. CITB reports AR/FWT/BWT/FR over task streams and initial/unseen sets; the local table does not currently compute the full CITB metric suite. | Mismatch / blocker |
| Seed | Seed 123 in configs. | Evidence found |
| W&B/tmux readiness | Current configs still use old `lora-published-setting-run_v2` groups; v10 config and tmux command must be written only after audit. | Not ready |
| Status | Do not launch full run. Current local Sequential LoRA remains a non-strict Llama LoRA adaptation, but a CITB T5 strict skeleton now exists at `configs/paper/lora_run_v10/instrdialog__citb_t5_sequential__s123.yaml` with CPU preflight runner `scripts/run_citb_t5_strict_baseline.py`. It is not strict until LM-adapted T5-small assets, official splits, FT-init trainer, and AR/FWT/BWT/FR metrics are implemented. | `strict-runner-skeleton-needs-citb-implementation-and-official-splits` |

## Replay LoRA

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | External source found: CITB defines Replay as saving random instances from each task in memory and jointly training new task data with old memory data. It reports Replay (10) and Replay (50) baselines for InstrDialog/InstrDialog++, but not a LoRA-specific replay baseline. | Benchmark/replay source found; LoRA variant not paper-verified |
| Official implementation path | Current path is unified local config plus `core/train.py`; example config `configs/paper/published_setting/instrdialog__replay_lora__s123.yaml`. `baselines/basic_baselines/replay_lora/method.py` confirms a single default adapter plus an in-memory replay buffer. | Not official-paper verified |
| Backbone | Config evidence: Llama-3.1-8B-Instruct. | Needs paper match |
| Adapter/prompt params | Config evidence: LoRA r16 alpha32 dropout0.05 target `q_proj`/`v_proj`. | Needs paper match |
| Optimizer/lr/batch/epochs/steps | Config evidence: lr 2e-4, batch 2, 1 epoch per segment. CITB uses the same initial instruction-tuned T5-small setup as other methods; exact local LoRA optimizer protocol is not part of the paper. | Mismatch / blocker |
| Replay protocol | Config evidence: replay enabled, buffer size 50, replay ratio 0.3, uniform sampling. Code evidence: current segment samples are added to the buffer before mixing, overflow drops oldest samples, and replay examples are chosen by `random.sample` at `round(len(current) * replay_ratio)`. CITB evidence: Replay (10)/(50) store random instances from each task and jointly train `M_init`, `M_seq`, and new task data. The local implementation has no `M_init` memory and adds current task samples before replay sampling. | Mismatch / blocker |
| Task order | Local streams exist for non-TOD37 benchmarks. | Needs paper order audit |
| Split/data path | Published-setting YAMLs point to train50/eval10 processed streams. | Needs paper split audit |
| Metrics/eval protocol | Same local seen-segment evaluator as Sequential LoRA; official replay baseline metric protocol is not certified. | Needs audit |
| Seed | Seed 123 in configs. | Evidence found |
| W&B/tmux readiness | Current configs use old v2 W&B groups; v10 command is not ready. | Not ready |
| Status | Do not launch full run. Current local Replay LoRA remains a non-strict Llama LoRA adaptation, but a CITB Replay(50) T5 skeleton now exists at `configs/paper/lora_run_v10/instrdialog__citb_t5_replay50__s123.yaml`. It is not strict until the T5 full-finetune runner, `M_init`/`M_seq` replay memory, official splits, and AR/FWT/BWT/FR metrics are implemented. | `strict-runner-skeleton-needs-citb-implementation-and-official-splits` |

## O-LoRA

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | Official/local source exists at `external_baselines/o_lora`; README describes AutoCL/O-LoRA task configs and `engine.py`; `external_baselines/official_smoke_plan.md` records commit `a712f54`. | Source found |
| Official implementation path | Official env `/root/autodl-tmp/conda_envs/lora_v10_o_lora` passes `src/run_uie_lora.py --help`; Seq-GLUE wrapper exists at `scripts/run_olora_seqglue_official.py`. | Env/runner smoke only |
| Backbone | Seq-GLUE config `configs/paper/lora_run_v10/seqglue__o_lora_official__s123.yaml` uses `t5-small`; O-LoRA README examples also reference `/workspace/MODELS/t5-small`. Need paper/backbone decision for each benchmark. | Needs audit |
| Adapter/prompt params | Seq-GLUE config uses LoRA dim 8, lambda1 0.5, lambda2 0.0. Need official LoRA targets and per-benchmark parameter grid/selection protocol. | Needs audit |
| Optimizer/lr/batch/epochs/steps | Seq-GLUE config uses lr 0.001, batch 8, 1 epoch, constant scheduler, no warmup. Need published setting confirmation. | Needs audit |
| Task order | Seq-GLUE bridge exported 8 segments to `data/olora/seqglue_s123`; other benchmarks lack official O-LoRA task config bridge. | Partial bridge |
| Split/data path | Seq-GLUE bridge uses `data/processed/seqglue_cl_tasks_train50_eval10.json` and outputs `data/olora/seqglue_s123`. `scripts/export_seqglue_to_olora.py --validate-only` now checks the expected 8-segment order, 50/10 train/eval counts, task-config coverage for train/dev/test, label files, non-empty splits, sampled schema, and sampled label membership. | Bridge smoke passed; paper equivalence still needs audit |
| Metrics/eval protocol | Wrapper currently runs official predict/generate path, and dry-run writes the exact official command manifest without launching training. Published O-LoRA metric target, generated-output parser, and v10 table mapping are still not audited. | Needs audit |
| Seed | Seed 123 in config. | Evidence found |
| W&B/tmux readiness | Dry-run command is available; do not start because Method x Benchmark checklist is incomplete and LFPT5 currently owns CUDA 0. | Not approved for full run |
| Status | O-LoRA / Seq-GLUE is `strict-preflight-ready-needs-full-run-and-paper-audit`; `scripts/audit_olora_seqglue_strict_preflight.py` validates the local bridge and dry-run manifest. It is not strict until official full run, paper hparam citation, label/instruction equivalence, and metric parser are complete. | Needs full run and audit |

## LB-CL

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | No dedicated official LB-CL source directory was found under `external_baselines/`. `docs/lora_run_v10_official_baseline_integration.md` records the blocker. | `faithful-port-required` |
| Official implementation path | Current unified file `baselines/advanced_baselines/lb_cl/method.py` is a scaffold with SVD/projection summaries, not a strict official reproduction. | Blocked |
| Backbone | No official LB-CL backbone is locally verified for these benchmarks. | Needs source/paper audit |
| Adapter/prompt params | Need sensitivity-aware parameter selection, low-boundary/projection path, triplet or contrastive objective if used, and exact LoRA/prompt parameters. | Blocked |
| Optimizer/lr/batch/epochs/steps | Not verified because official code/protocol is absent. | Blocked |
| Task order | Cannot be certified without official code or faithful port protocol. | Blocked |
| Split/data path | Local benchmark data may exist, but LB-CL strict data mapping is not defined. | Blocked |
| Metrics/eval protocol | Cannot certify strict metrics until implementation and protocol are fixed. | Blocked |
| Seed | Seed 123 can be used later, but no strict runner exists. | Not ready |
| W&B/tmux readiness | No strict tmux command should be written or launched. | Blocked |
| Status | No LB-CL full run may be called strict. Obtain official source or implement and audit a faithful port first. | `faithful-port-required` |

## Progressive Prompts

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | Official source exists at `external_baselines/progressive_prompts`; README identifies Progressive Prompts ICLR 2023 and describes soft prompts concatenated across tasks. | Source found |
| Official implementation path | Candidate official entry `external_baselines/progressive_prompts/T5_codebase/train_t5_cl.py`; env setup command exists in `scripts/prepare_official_baseline_envs.sh`. | Not bridged |
| Backbone | README examples mention T5-large and BERT-base; local unified configs use Llama-3.1-8B-Instruct and are not strict. | Needs paper/backbone audit |
| Adapter/prompt params | Must implement trainable soft prompt module, prompt length/init, progressive concatenation/routing, and task-specific prompt preservation. | Missing bridge |
| Optimizer/lr/batch/epochs/steps | README examples mention prompt size 10 for 10 epochs in T5 example; exact benchmark setting still needs paper/code audit. | Needs audit |
| Task order | No official bridge for InstrDialog, InstrDialog++, TRACE, MultiWOZ NLG, Seq-GLUE, or TOD37. | Missing |
| Split/data path | Local published-setting YAMLs exist but point to unified scaffold. | Not strict |
| Metrics/eval protocol | Official evaluation scripts are not mapped to v10 metrics. | Needs bridge |
| Seed | Seed 123 in local configs only. | Not enough |
| W&B/tmux readiness | No strict command should be launched. | Not ready |
| Status | Source exists. Seq-GLUE now has `configs/paper/lora_run_v10/seqglue__progressive_prompts_official__s123.yaml` and `scripts/preflight_official_prompt_baselines.py` maps the 8 local Seq-GLUE segments to official T5 task names and emits the official command. It remains non-strict until paper task-order/hparams and `results_dict.npy` metric parsing are implemented. | `strict-runner-skeleton-needs-paper-audit-and-metric-parser` |

## Continual-T0

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | Official source exists at `external_baselines/continual_t0`; README cites arXiv 2205.12393 and checkpoint `ThomasNLG/CT0-11B`. | Source found |
| Official implementation path | README points to a Colab and Google Drive material; env setup command exists in `scripts/prepare_official_baseline_envs.sh`. | Not bridged |
| Backbone | Need official T0/T5 checkpoint decision; local unified configs use Llama-3.1-8B-Instruct and are not strict. | Blocked |
| Adapter/prompt params | Continual-T0 is not a LoRA/prompt baseline in the local scaffold; need official templates, mixture, and rehearsal design. | Needs audit |
| Optimizer/lr/batch/epochs/steps | README says parameters are in the paper; local runner has not audited them. | Needs audit |
| Task order | Official mixture/task stream not mapped to requested benchmarks. | Missing |
| Split/data path | Need Google Drive processed data or reproducible formatting with rehearsal. | Blocked |
| Metrics/eval protocol | README says evaluation scripts are in provided material; not integrated locally. | Needs bridge |
| Seed | Seed 123 in local scaffold only. | Not enough |
| W&B/tmux readiness | No strict command should be launched. | Not ready |
| Status | Official source exists. Seq-GLUE now has `configs/paper/lora_run_v10/seqglue__continual_t0_official__s123.yaml` and preflight records README/setup/requirements readiness, but the official Colab/Drive assets, CT0 checkpoint, mixture/rehearsal formatting, and metric parser are still missing. | `strict-runner-skeleton-needs-official-assets` |

## LFPT5

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | Official source exists at `external_baselines/lfpt5`; README identifies ICLR 2022 LFPT5 and LM-adapted T5 prompt tuning. | Source found |
| Official implementation path | Wrapper `scripts/run_lfpt5_published_setting.py` calls `external_baselines/lfpt5/citb_bridge/run_continual.py` in env `lfll_1`. | Bridge exists |
| Backbone | Config evidence: LM-adapted T5-large checkpoint `assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin`. | Evidence found |
| Adapter/prompt params | Config evidence: prompt tuning with `prompt_number: 300`; no LoRA. | Evidence found |
| Optimizer/lr/batch/epochs/steps | InstrDialog++ config records batch 2, but optimizer/lr are bridge defaults and command uses `--max-epoch 4`; exact paper setting not yet proven for InstrDialog++. | Needs audit |
| Task order | InstrDialog++ stream path `data/processed/citb_cl_38_random_tasks_train50_eval10.json`; exact paper protocol for this benchmark still needs citation. | Needs audit |
| Split/data path | train50/eval10 processed stream is configured. | Evidence found but needs paper match |
| Metrics/eval protocol | Current bridge writes per-segment metrics, but LFPT5 paper scoring and benchmark metric mapping are not fully audited. | Needs audit |
| Seed | Seed 123 in configs. | Evidence found |
| W&B/tmux readiness | Active InstrDialog++ run uses W&B project/group `lora-run_v10`; because checklist is incomplete it stays `running-needs-setting-verification`. | Running exception |
| Status | Do not certify as strict yet. Other LFPT5 benchmarks need v10 audit/rerun; Seq-GLUE fix3 is user-stopped partial; TOD37 is data-blocked. | Mixed |

## Ours

| Checklist item | Evidence | Status |
| --- | --- | --- |
| Published paper/source | Project method, not an external published baseline reproduction. | Not applicable |
| Official implementation path | Local project implementation/configs. | Needs comparison audit |
| Backbone | Local configs must be audited per benchmark before final comparison. | Needs audit |
| Adapter/prompt params | Project-specific; not a baseline-paper setting. | Needs audit |
| Optimizer/lr/batch/epochs/steps | Need v10 comparison protocol and clean run records. | Needs audit |
| Task order | Local benchmark streams exist for non-TOD37 benchmarks. | Needs audit |
| Split/data path | Local processed streams exist; TOD37 missing. | Partial |
| Metrics/eval protocol | Must match the table protocol for each benchmark. | Needs audit |
| Seed | Seed 123 target. | Planned |
| W&B/tmux readiness | Do not launch until baseline order and our-method protocol are approved. | Not ready |
| Status | Track separately from strict published baseline reproduction claims. | `needs-paper-setting-audit` |

## Retired Benchmark: TOD37

TOD37 has been removed from the active reproduction benchmark matrix by user decision. Existing `tod37` scripts/manifests are retained only as archival utilities and should not block strict alignment or launch planning.
