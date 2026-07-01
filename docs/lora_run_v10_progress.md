# lora-run_v10 Progress

Updated: 2026-06-19 11:27 CST

## Main-Control Pass

- Updated `docs/lora_run_v10_master_plan.md` with the latest local smoke result and a Method x Benchmark executability matrix for Sequential LoRA, Replay LoRA, O-LoRA, LB-CL, Progressive Prompts, Continual-T0, LFPT5, and Ours across InstrDialog, InstrDialog++, TRACE, MultiWOZ NLG, Seq-GLUE, and TOD37.
- Ran `python scripts/smoke_published_setting_pipeline.py --skip-external`; it passed. The smoke verified local config/data loading for all published-setting YAMLs, including Seq-GLUE 8 segments, TRACE 8 segments, MultiWOZ 5 domains, InstrDialog 19 segments, and InstrDialog++ 38 segments.
- Confirmed tmux `lora_run_v10_queue` is still running `lora_run_v10_seqglue_lfpt5_s123`; no new full-run tmux was started because the v10 LFPT5 GPU job is active.
- Confirmed tmux `lora_run_v10_blocked_unlock_queue` is only waiting for the active GPU job and remains outside this pass's edit boundary.

## Blocked Queue Unlock

- Source audit: historical supervisor `blocked=7` at 2026-06-17 16:29 referred to the 7 TRACE published-setting rows (`trace_full_{ours,o_lora,lb_cl,progressive_prompts,continual_t0,sequential_lora,replay_lora}_s123`) while TRACE processed data was not ready. These rows now have `final_metrics.json` and are completed in the v2 reference status.
- Current blocked queue item: `published_instrdialogpp_lfpt5_s123` (LFPT5 / InstrDialog++ / seed 123). The blocker was a partial LFPT5 run without `final_metrics.json`; the previous W&B/config issues were fixed and the config now targets project/group `lora-run_v10`.
- Archive action: moved the inactive partial run from `results/runs/published_instrdialogpp_lfpt5_s123/` to `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_051612_blocked_unlock_requeue/run/`. The archive manifest records the original path and reason.
- Restart action: updated `results/tables/published_setting_run_v2_gap_manifest.csv` and `results/tables/published_setting_run_v2_gap_status.csv` for this row to `queued`, with W&B project/group `lora-run_v10`.
- tmux: `lora_run_v10_blocked_unlock_queue` is waiting for the active `lora_run_v10_seqglue_lfpt5_s123` training to release the GPU, then will run `scripts/run_published_setting_run_v2_gap_queue.sh` for the LFPT5 gap item.
- Remaining blocker: no missing data/checkpoint/official-code blocker found for this row; execution is deferred only by the active v10 LFPT5 GPU job.

## Current Run

- tmux session: `lora_run_v10_queue`
- active run: `lora_run_v10_seqglue_lfpt5_s123`
- method / benchmark / seed: LFPT5 / Seq-GLUE / 123
- config: `configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml`
- log: `results/logs/lora_run_v10/lora_run_v10_seqglue_lfpt5_s123.log`
- run dir: `results/runs/lora_run_v10_seqglue_lfpt5_s123/`
- W&B: project `lora-run_v10`, group `lora-run_v10_seqglue_lfpt5`, run `https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-run_v10/runs/naaocm1y`
- status: running; reached at least `LFPT5 segment 6 (super_glue_cb)` at 2026-06-18 05:19:50.

## Monitoring Worker Check - 2026-06-18 05:19 CST

- `tmux capture-pane -t lora_run_v10_queue` shows the LFPT5/Seq-GLUE v10 job still active with W&B project `lora-run_v10`, group `lora-run_v10_seqglue_lfpt5`, run id `naaocm1y`.
- Latest tmux/log milestone: `LFPT5 segment 5 (super_glue_wic)` started at 2026-06-18 05:18:03 CST. No traceback or failure appears after the initial harmless pre-run `pgrep` check.
- Active processes still include `python scripts/run_lfpt5_published_setting.py --config configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml` and the LFPT5 bridge process on `--cuda 0`.
- `results/runs/lora_run_v10_seqglue_lfpt5_s123/metrics.jsonl` has completed segment rows for 0-4; `final_metrics.json` and `results/tables/lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv` do not exist yet, so the run is not complete.
- Decision: healthy in-progress run; no new full run was launched to avoid competing for the active GPU. `lora_run_v10_blocked_unlock_queue` should continue waiting for GPU release.
- Next suggested checkpoint: 2026-06-18 05:23-05:25 CST, or earlier if tmux reports segment 7/completion/failure.

## Monitoring Worker Check - 2026-06-18 05:20 CST

- `tmux capture-pane -pt lora_run_v10_queue` shows the LFPT5/Seq-GLUE v10 job still active with W&B project `lora-run_v10`, config group `lora-run_v10_seqglue_lfpt5`, run id `naaocm1y`.
- Latest tmux/log milestone: `LFPT5 segment 6 (super_glue_cb)` started at 2026-06-18 05:19:50 CST. No `Traceback`, `ERROR`, CUDA OOM, or completion line appears in `results/logs/lora_run_v10/lora_run_v10_seqglue_lfpt5_s123.log`.
- Active processes still include `python scripts/run_lfpt5_published_setting.py --config configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml` and the LFPT5 bridge process on `--cuda 0`.
- `results/runs/lora_run_v10_seqglue_lfpt5_s123/metrics.jsonl` currently has completed segment rows for 0-5; `final_metrics.json` and `results/tables/lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv` are not present yet, so the run is not complete.
- `lora_run_v10_blocked_unlock_queue` remains in its GPU wait loop and has not started `published_instrdialogpp_lfpt5_s123` yet.
- Decision: healthy in-progress run; no new full run was launched.

## Audit Summary

- Main repository: `/root/autodl-tmp/Lora-code`.
- Existing `published_setting_run_v2` results are useful for reference but are not compliant with this request because their W&B project is `lora-published-setting-run_v2`, not `lora-run_v10`.
- The local published-setting README explicitly marks O-LoRA, LB-CL, Progressive Prompts, and Continual-T0 unified-entry versions as scaffold or incomplete paper reproductions. These should not be reported as strict published-paper reproductions until their official settings/implementations are aligned.
- LFPT5 is the strictest available first batch because it uses the separate T5 prompt-tuning path and an LM-adapted T5 checkpoint rather than the unified Llama-LoRA scaffold.
- MultiWOZ NLG still lacks slot error in the local published-setting notes; BLEU/ROUGE are available.

## Fixes Applied

- `external_baselines/lfpt5/citb_bridge/run_continual.py`: added real W&B logging via `WandbTracker`, logs per-segment rows/final metrics/artifacts, and escapes generated replay memory rows.
- `external_baselines/lfpt5/Summarization/model.py`: resizes T5 embeddings using the maximum tokenizer id after adding LFPT5 task tokens and clones labels before replacing pad ids with `-100`, avoiding CUDA device-side asserts from in-place label mutation or undersized embeddings.
- `scripts/run_lora_run_v10_queue.sh`: added a v10 tmux queue and fixed process-wait logic so it does not match itself.
- `configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml`: created a non-overwriting v10 config with W&B project `lora-run_v10`.
- `results/tables/lora_run_v10_manifest.csv` and `results/tables/lora_run_v10_status.csv`: added first-batch tracking.

## Conflict Handling

- Stopped the non-compliant old `published_setting/instrdialogpp__lfpt5__s123` process/session (`lora_run_v10_gap_lfpt5_unlock`) because it used the old config/project and would compete with the v10 GPU run.

## Blocked / Partial Unlock Log

- Historical supervisor `blocked=7` rows were the TRACE full published-setting cells (`trace_full_ours_s123`, `trace_full_o_lora_s123`, `trace_full_lb_cl_s123`, `trace_full_progressive_prompts_s123`, `trace_full_continual_t0_s123`, `trace_full_sequential_lora_s123`, `trace_full_replay_lora_s123`) while TRACE processed data was not ready. They now have `final_metrics.json` and are completed in the v2 reference tables.
- Historical partial rows `published_instrdialogpp_sequential_lora_s123` and `full_multiwoz_ours_s123` now also have completed v2 outputs; the MultiWOZ partial archive already exists at `archives/partial_runs/full_multiwoz_ours_s123_20260617_161057/`.
- The active LFPT5 partial/blocker handled in this pass was `published_instrdialogpp_lfpt5_s123`. I archived the non-tmux partial and three short failed restarts under `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_050712/`, `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_050820_wandb_settings_failed/`, `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_050919_wandb_missing_init/`, and `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_051038_wandb_empty_tag/`.
- Fixes applied for that blocker: `configs/paper/published_setting/instrdialogpp__lfpt5__s123.yaml` now targets `lora-run_v10`, `scripts/run_published_setting_run_v2_gap_queue.sh` defaults to `lora-run_v10`, `scripts/gen_published_setting_run_v2_gap_manifest.py` regenerates v10 project/group values, `core/wandb_tracker.py` tolerates older wandb settings and filters empty tags, and official `wandb==0.26.1` is installed in `lfll_1`.
- `published_instrdialogpp_lfpt5_s123` restart was validated in tmux and reached W&B project `lora-run_v10`. The inactive partial was archived at `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_051612_blocked_unlock_requeue/`, and the row is now requeued for `lora_run_v10_blocked_unlock_queue` after the active Seq-GLUE LFPT5 run releases the GPU.

## Next Steps

1. Keep monitoring `lora_run_v10_queue` until Seq-GLUE/LFPT5 completes all 8 tasks and writes `final_metrics.json`.
2. Compare `results/tables/lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv` against the published-setting/reference LFPT5 Seq-GLUE table; if the gap is large, inspect split/order, prompt length, replay memory, checkpoint loading, and metric computation before expanding the matrix.
3. Only after this first run is stable, choose the next batch from official/full-setting candidates; do not promote scaffold O-LoRA/LB-CL/PP/C-T0 results as paper-aligned.

### Monitor 2026-06-18 05:23:30 CST
- lora_run_v10_seqglue_lfpt5_s123: tmux latest output shows still running; latest observed segment 7 (super_glue_copa, task_idx=7). No obvious failure traceback after training start.
- Result files: results/runs/lora_run_v10_seqglue_lfpt5_s123/final_metrics.json missing; results/tables/lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv missing.
- lora_run_v10_blocked_unlock_queue: still waiting for GPU (active training owns GPU; sleep 60s); published_instrdialogpp_lfpt5_s123 has not started in the captured output.
- Next step: keep monitoring until seqglue finishes and releases GPU; do not restart or modify metrics unless a clear failure appears.

### Monitor 2026-06-18 05:23:06 CST
- : tmux latest output shows still running; latest observed segment 7 (, task_idx=7). No obvious failure traceback after training start.
- Result files:  missing;  missing.
- : still waiting for GPU ();  has not started in the captured output.
- Next step: keep monitoring until seqglue finishes and releases GPU; do not restart or modify metrics unless a clear failure appears.


### LFPT5 / Seq-GLUE Completion - 2026-06-18 05:25 CST
- Completion: `lora_run_v10_seqglue_lfpt5_s123` wrote `final_metrics.json` and `lora_run_v10_seqglue_lfpt5_s123_segment_metrics.csv`; file mtime is 2026-06-18 05:23:55 CST and the LFPT5 bridge logged final write at 05:23:59 CST.
- W&B: project `lora-run_v10`, group `lora-run_v10_seqglue_lfpt5`, run `https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-run_v10/runs/naaocm1y`.
- Final metrics: `eval.current_score=0.0`, `eval.seen_avg_score=0.0`, `eval.current_task_aware_score=0.0`, `eval.seen_avg_task_aware_score=0.0`, `eval.forgetting=0.0`, `eval.task_aware_forgetting=0.0`, `eval.num_seen_segments=8`, `eval.token_f1_mean=0.007601010101010101`; final segment is `super_glue_copa`.
- Segment metrics: all 8 segments have `eval.current_score=0.0` and `eval.current_task_aware_score=0.0`; `eval.token_f1_mean` ranges from 0.0 to 0.015202020202020203 and averages about 0.007279.
- Target/reference search: `docs/lora_run_v10_master_plan.md` identifies LFPT5 / Seq-GLUE as the P0 published-setting target and says to compare against prior LFPT5 Seq-GLUE/reference outputs, but no strict numeric published target was found in `docs/master_plan/progress`, `results/tables`, `configs`, or `README`. The local historical `published_seqglue_lfpt5_s123` table matches the v10 zero-score pattern, so it is not a strict published target.
- Preliminary gap judgment: without a numeric published target the exact gap cannot be certified, but all classification-style scores being zero and token F1 near zero is clearly suspicious. Most likely follow-up directions are LFPT5 generation-to-label parsing, task template/answer verbalizer mapping, Seq-GLUE split/order alignment, checkpoint/prompt loading, replay memory behavior, and metric computation; do not edit result numbers.
- Next queue state: `lora_run_v10_blocked_unlock_queue` detected GPU release and started `published_instrdialogpp_lfpt5_s123` at 2026-06-18 05:24:12 CST. W&B project/group are configured as `lora-run_v10`; W&B run id is `jv8lz4oj`, and the bridge reached segment 0 (`task1549_wiqa_answer_generation_missing_step`) by 05:24:19 CST.

### LFPT5 Prompt-Init Fix / Rerun - 2026-06-18 05:30 CST
- Zero-score audit: `lora_run_v10_seqglue_lfpt5_s123` is not paper-aligned; all 8 Seq-GLUE classification scores are 0 and token F1 is near zero. The result remains in place and was not edited.
- Root cause found: `external_baselines/lfpt5/citb_bridge/run_continual.py` reused the LFPT5 `Summarization` prompt initialization for Seq-GLUE. That initialized segment 0 with `["summarization", "glue_sst2"]` and omitted the official classification-style seed text plus label verbalizers (`sentence classification`, task name, labels). This is a real bridge bug for classification streams.
- Fix applied: the bridge now detects Seq-GLUE / `lfpt5.task_family: classification`, initializes prompt embeddings with classification label verbalizers, and writes `scored_details_by_segment` with prediction/gold/normalized fields into `eval_metrics.json` for future audits. `configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml` is explicitly marked `task_family: classification`.
- Seq-GLUE restart: created `configs/paper/lora_run_v10/seqglue__lfpt5__s123_fix1.yaml` with run name `lora_run_v10_seqglue_lfpt5_s123_fix1`; tmux `lora_run_v10_seqglue_lfpt5_fix1` started at 05:29 CST. W&B project/group remain `lora-run_v10` / `lora-run_v10_seqglue_lfpt5`; W&B run id is `yaybfwya`. Live log confirms prompt seeds `["sentence classification", "glue_sst2", "negative", "positive"]`.
- InstrDialog++ risk handling: the old `published_instrdialogpp_lfpt5_s123` run (`jv8lz4oj`) had already produced zero scores on the first two segments under the old bridge. It was safely stopped and archived at `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_052853_lfpt5_prompt_init_bug/`; gap manifest/status were returned to `queued` with W&B project/group `lora-run_v10` / `lora-run_v10`.
- Superseded: `fix1` was used as a diagnostic probe only; see the next section for the official-hparam `fix2` restart and current queue state.

### LFPT5 Official-HParam Fix2 - 2026-06-18 05:33 CST
- `fix1` early diagnostic: segment 0/1 still scored 0.0, but the new prediction details showed SST-2 predictions were mostly copied input sentences or punctuation rather than `positive` / `negative`. That exposed a second bridge issue: the wrapper defaults were `lr=5e-5`, `gradient_accumulation_steps=1`, `kd_lamda=0.05`, `max_epoch=4`, far from the official LFPT5 classification script (`lr=0.5`, `gradient_accumulation_steps=4`, `kd_lamda=0.01`, `max_epoch=1280`). `fix1` was stopped and archived at `archives/partial_runs/lora_run_v10_seqglue_lfpt5_s123_fix1_20260618_053218_undertrained_probe/`.
- Config fix: `configs/paper/lora_run_v10/seqglue__lfpt5__s123.yaml` now records `task_family: classification`, `lr: 0.5`, `kd_lamda: 0.01`, `gradient_accumulation_steps: 4`, and `bridge_max_epoch: 1280`. A new runnable config `configs/paper/lora_run_v10/seqglue__lfpt5__s123_fix2.yaml` uses run name `lora_run_v10_seqglue_lfpt5_s123_fix2`.
- Current rerun: tmux `lora_run_v10_seqglue_lfpt5_fix2` is running with W&B project/group `lora-run_v10` / `lora-run_v10_seqglue_lfpt5`, run id `wmtgbcet`. `run_manifest.json` confirms `--max-epoch 1280`; live log confirms classification labels `['negative', 'positive']` and prompt seeds `['sentence classification', 'glue_sst2', 'negative', 'positive']`.
- Queue state: tmux `lora_run_v10_blocked_unlock_queue` was restarted as a wait loop for `fix2`; it will only launch `scripts/run_published_setting_run_v2_gap_queue.sh` after the `fix2` LFPT5 process exits, so `published_instrdialogpp_lfpt5_s123` remains queued and will not compete for GPU.
- Risk note: because `fix2` restores official classification training length, segment 0 may take much longer than the previous 4-epoch smoke/probe. The next useful checkpoint is either segment 0 completion with non-copy predictions, or a resource/time decision if the full official-length Seq-GLUE rerun is too slow.

### LFPT5 NaN Guard Fix3 - 2026-06-18 17:12 CST
- Failure observed: `lora_run_v10_seqglue_lfpt5_s123_fix2` completed segment 0 `glue_sst2` at 1.0 and segment 1 `glue_mrpc` at 0.7, but segment 2 `glue_rte` wrote `train_loss_mean/lm_loss_mean/kd_loss_mean=NaN` and all seen eval scores collapsed to 0.0. Segment 3 `glue_cola` then failed during pseudo-memory sampling with CUDA `probability tensor contains either inf, nan or element < 0`, so fix2 is failed diagnostic output only.
- Root cause: the CITB bridge runs Seq-GLUE classification through `external_baselines/lfpt5/Summarization/model.py`; unlike the official `Classification/model.py`, that KD path took `softmax(...).log()` without adding `sys.float_info.min`, so zero probabilities could produce `-inf/NaN`. The bridge also did not fail fast on non-finite loss/gradient/prompt embeddings, allowing the RTE NaN prompt to be checkpointed and reused by CoLA generation.
- Fix applied: `external_baselines/lfpt5/Summarization/model.py` now adds the same KD epsilon and converts non-finite KD to an on-device zero scalar. `external_baselines/lfpt5/citb_bridge/run_continual.py` now validates loss, gradient, and prompt embeddings, fixes the gradient-accumulation step condition to `(step + 1) % grad_accum == 0`, scales loss by accumulation, and refuses to save/generate with non-finite prompt weights.
- InstrDialog++ decision: the automatically unlocked `published_instrdialogpp_lfpt5_s123` run inherited the unsafe bridge, so it was stopped before completion and archived at `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_170854_stopped_after_seqglue_nan_guard/`. Its gap manifest/status row was returned to `queued` for a clean rerun after the LFPT5 guard fix; no partial metrics should be used.
- Clean rerun: created `configs/paper/lora_run_v10/seqglue__lfpt5__s123_fix3.yaml` with run name `lora_run_v10_seqglue_lfpt5_s123_fix3`. tmux `lora_run_v10_seqglue_lfpt5_fix3` is running on CUDA 0 with `--max-epoch 1280`; W&B project/group are `lora-run_v10` / `lora-run_v10_seqglue_lfpt5`, run id `fc8g2yup`.
- Startup check: fix3 reached segment 0 `glue_sst2`, exported 8 segments, and confirmed classification prompt seeds `['sentence classification', 'glue_sst2', 'negative', 'positive']`. Next monitor point is segment 0 metrics; if any `FloatingPointError` appears, treat it as a guard-triggered blocker and inspect the first non-finite loss details rather than restarting blindly.

### Monitor 2026-06-18 17:19 CST
- Independent state check: no active `published_instrdialogpp_lfpt5_s123` process was found. Its gap manifest/status row is `queued` with W&B project/group `lora-run_v10` / `lora-run_v10`, and the unsafe partial archive exists at `archives/partial_runs/published_instrdialogpp_lfpt5_s123_20260618_170854_stopped_after_seqglue_nan_guard/`.
- Active GPU run: tmux `lora_run_v10_seqglue_lfpt5_fix3` is still running `run_lfpt5_published_setting.py --config configs/paper/lora_run_v10/seqglue__lfpt5__s123_fix3.yaml`; the bridge process owns CUDA 0 and W&B run `fc8g2yup`. No `metrics.jsonl` row has been written yet, so segment 0 training is still in progress.
- Label/token audit: all Seq-GLUE train/eval outputs are non-empty. RTE labels are `entailment` / `not_entailment`; CoLA labels are `acceptable` / `not_acceptable`; all label verbalizers tokenize within the local T5 vocabulary and are far below `prompt_number=300`, so there is no evidence of empty verbalizers or target-id range violations.
- Next monitor point: wait for the first fix3 segment row. If segment 0 completes, verify `glue_sst2` score and prediction details before letting the rest of the queue proceed; if a `FloatingPointError` fires, keep the run as a blocker with the first non-finite loss/gradient context rather than blind-restarting.

## Strict Paper Alignment Gap Repair Plan - 2026-06-19 00:20 CST

User correction: gaps must not remain as caveats. Each non-strict cell must become either a concrete repair task, a clean queued run, or an explicit blocker with the missing official implementation/data/metric named.

Current execution boundary:

- Do not start another GPU full run while `lora_run_v10_seqglue_lfpt5_s123_fix3` owns CUDA 0.
- Do not promote old `published_setting_run_v2` outputs as `lora-run_v10` strict results; they are reference/audit inputs only unless rerun or revalidated under the current protocol.
- Do not report unified-pipeline scaffold outputs for O-LoRA, LB-CL, Progressive Prompts, or Continual-T0 as published-paper reproductions.

Method-level repair tasks:

- Sequential LoRA: verify the exact published baseline protocol per benchmark: backbone, optimizer, LoRA rank/alpha/dropout, task order, replay-free training budget, and metrics. Then create v10 configs and queue full single-seed reruns for benchmarks whose protocol can be matched locally.
- Replay LoRA: verify official replay memory size, sampling rule, update timing, task stream, and metrics. Existing local replay is a baseline candidate, but it must be audited before strict reporting.
- O-LoRA: current unified implementation is only an orthogonal/scaffold hook. Strict reproduction requires official O-LoRA code/settings or a faithful port of its orthogonal subspace update, backbone, task order, and metric protocol.
- LB-CL: current unified implementation is scaffold. Strict reproduction requires the official sensitivity/projection/triplet pipeline, matching backbone and hyperparameters, and paper task/metric setup.
- Progressive Prompts: current unified implementation is scaffold. Strict reproduction requires real soft-prompt modules, progressive prompt composition/routing, prompt length/init/training budget, and paper-specific evaluation.
- Continual-T0: current unified implementation is scaffold. Strict reproduction requires T0/T5 checkpoint, official task mixture, rehearsal percentage, prompt/template protocol, and paper metrics.
- LFPT5: strict first target remains active. Seq-GLUE `fix3` is the current clean run after prompt-init, official classification hyperparameter, and NaN-guard fixes. InstrDialog++ is queued for a clean rerun after Seq-GLUE releases GPU. Existing LFPT5 InstrDialog/TRACE/MultiWOZ v2 outputs are reference until v10 audit/rerun.
- Ours: project method, not a baseline-paper reproduction. It should be run and audited for our comparison table, but reported separately from official baseline reproduction claims.

Benchmark-level blockers:

- InstrDialog / InstrDialog++: data/configs are locally available. LFPT5 can use the external runner; other methods need strict protocol audit before rerun.
- TRACE: data/configs are locally available, but strict claims require method-specific protocol and metric/delta audit.
- MultiWOZ NLG: BLEU/ROUGE are available, but slot error is still a metric blocker for paper-aligned dialogue NLG claims.
- Seq-GLUE: active LFPT5 strict candidate; other methods require official protocol audit before queueing.
- TOD37: blocked by missing TM19/TM20/SGD preprocessing/data; cannot be strict until data pipeline is completed.

Immediate next actions:

1. Continue monitoring `lora_run_v10_seqglue_lfpt5_s123_fix3`; if MRPC is confirmed stalled, stop/archive it as a diagnostic run and inspect the training loop before a new clean rerun.
2. While GPU is occupied, build a no-GPU strict alignment tracker from the method-level repair tasks above.
3. After GPU release, prioritize clean full single-seed runs in this order: LFPT5 Seq-GLUE completion/repair, LFPT5 InstrDialog++ clean rerun, LFPT5 InstrDialog/TRACE/MultiWOZ v10 audit/rerun, then official-implementation repairs for non-LFPT5 baselines.

Tracker created:

- `results/tables/lora_run_v10_strict_alignment_tracker.csv` now records every requested Method x Benchmark cell with one of: `running`, `queued`, `old-reference-only`, `needs-audit`, `scaffold-not-strict`, `blocked-metric`, or `blocked-data`.
- This tracker is the working source for future status reports. A cell can only move to strict completed after a clean `lora-run_v10` run or a documented v10 audit confirms that the result follows the published paper protocol and matches the target paper metrics.

## Strict Repair Work - 2026-06-19 00:38 CST

Execution boundary respected: no new GPU run was started and the active LFPT5 / Seq-GLUE `fix3` job was not stopped or modified.

No-GPU repairs completed:

- MultiWOZ NLG slot error: implemented AdapterCL-style required act-value missing rate in `core/metrics_utils.py` and wired it into `core/evaluate.py` as `slot_error_rate`; future unified runs will write `eval.slot_error_rate` and `extra.slot_error_count`. Added tests in `tests/test_metrics_utils.py`. This does not rewrite historical BLEU/ROUGE-only result tables.
- MultiWOZ blocker status: updated `configs/paper/published_setting/README.md` and `results/tables/lora_run_v10_strict_alignment_tracker.csv`; MultiWOZ cells are now metric-ready but still require clean v10 reruns and method-specific protocol audits.
- TOD37 data blocker: added `scripts/convert_tod37_to_stream.py`, a no-download readiness checker that writes `results/tables/tod37_preprocess_blocker_manifest.json` and names missing TM19/TM20/SGD/MultiWOZ raw paths. Export remains blocked until AdapterCL/ToDCL raw data exists.
- Non-LFPT5 official baseline blocker: added `docs/lora_run_v10_official_baseline_integration.md` and linked it from `external_baselines/README.md`. O-LoRA, Progressive Prompts, and Continual-T0 official source directories exist but are not bound to the v10 runner; LB-CL has no dedicated official source found locally. The unified entries remain scaffold-only.

Remaining blockers:

- TOD37 strict runs need TM19/TM20/SGD raw data and the AdapterCL joint preprocessing output before any Method x TOD37 cell can be queued.
- O-LoRA / Progressive Prompts / Continual-T0 need official runner bridges or faithful ports before their scaffold rows can move to strict rerun.
- LB-CL needs official code or a paper-faithful port design; the current SVD/projection scaffold is not enough for a published-paper claim.
- MultiWOZ strict numbers still require full single-seed v10 reruns with BLEU/ROUGE/slot error after CUDA 0 is free.

## Strict Repair Work - 2026-06-19 01:46 CST

User correction reaffirmed: every non-strict reproduction gap must be actively repaired, then full single-seed rerun and compared against the published paper result. If the gap remains large, repair and rerun again.

No-GPU official-entry smoke was run with:

```bash
bash scripts/smoke_external_baselines.sh all
```

Smoke result:

- O-LoRA: official files compile (`engine.py`, `src/run_uie_lora.py`), but `--help` needs an isolated official environment because `nltk` is missing in the current global env.
- Progressive Prompts: official T5/BERT entry files compile, but `--help` needs the official old dependency stack (`transformers.AdamW`, `AutoAdapterModel` are missing from the current global env).
- Continual-T0: `setup.py` compiles; still needs official T0/T5 checkpoint, mixture data, and rehearsal protocol before full strict rerun.
- LFPT5: official conversion/classification shell smoke passes; active strict Seq-GLUE `fix3` continues to own CUDA 0.
- AdapterCL/ToDCL dialogue: `train.py` compiles, but `--help` needs isolated deps (`pytorch_lightning` missing). This is the path needed for TOD37/Dialogue NLG strict setup.
- LAMOL, TRACE/RCL, InfLoRA, ARPER Dialogue NLG, and BNM reference lightweight syntax/compile checks pass where applicable.

Repair implication:

- The next no-GPU repair step is to create isolated environment specs/runner wrappers for O-LoRA, Progressive Prompts, and AdapterCL rather than trying to run them in the current project env.
- LB-CL remains the hardest blocker because no dedicated official source is present locally; it requires obtaining official code or writing a documented faithful port before any strict run.
- Full GPU runs remain blocked behind `lora_run_v10_seqglue_lfpt5_s123_fix3`; do not start competing training until that run finishes, fails, or is archived.

## Strict Repair Work - 2026-06-19 01:50 CST

User requested that all official-environment blockers be resolved until the methods can start strict full runs.

No-GPU repair completed:

- Added `scripts/prepare_official_baseline_envs.sh`.
- The script supports `ACTION=check` and `ACTION=create` for `o_lora`, `progressive_prompts`, `adaptercl_dialogue`, and `continual_t0`.
- `ACTION=check bash scripts/prepare_official_baseline_envs.sh all` passed and verified:
  - O-LoRA official requirements and `src/run_uie_lora.py` exist.
  - Progressive Prompts official `environment.yaml`, T5 entry, and BERT entry exist.
  - AdapterCL/ToDCL requirements, `train.py`, and the TOD37 readiness script exist.
  - Continual-T0 requirements and `setup.py` exist, but checkpoint/data blockers remain.

Environment creation commands prepared:

```bash
ACTION=create bash scripts/prepare_official_baseline_envs.sh o_lora
ACTION=create bash scripts/prepare_official_baseline_envs.sh progressive_prompts
ACTION=create bash scripts/prepare_official_baseline_envs.sh adaptercl_dialogue
ACTION=create bash scripts/prepare_official_baseline_envs.sh continual_t0
```

Execution note: `ACTION=create` may install old PyTorch/transformers stacks and can be slow or network-dependent. It should be run when resource contention with the active LFPT5 training is acceptable. It still does not download benchmark data/checkpoints or start training.

### O-LoRA Env Attempt - 2026-06-19 02:19 CST

- Attempted `ACTION=create bash scripts/prepare_official_baseline_envs.sh o_lora`.
- Conda env `lora_v10_o_lora` was created, but official `requirements.txt` installation failed with `OSError: [Errno 28] No space left on device` while installing large PyTorch/CUDA dependency wheels.
- This is now a storage blocker, not a source-code blocker. Do not mark O-LoRA as runnable until either disk space is freed or the environment script is changed to install a smaller CPU/CUDA-compatible torch stack that satisfies the official O-LoRA runner.
- No cleanup was performed automatically to avoid deleting user or active experiment artifacts.

### O-LoRA Env Storage Fix - 2026-06-19 02:43 CST

- Updated `scripts/prepare_official_baseline_envs.sh` to support `ENV_ROOT` and `PIP_CACHE_DIR`.
- `ENV_ROOT=/root/autodl-tmp/conda_envs PIP_CACHE_DIR=/root/autodl-tmp/pip_cache ACTION=check bash scripts/prepare_official_baseline_envs.sh all` passed.
- Next O-LoRA retry should use:

```bash
ENV_ROOT=/root/autodl-tmp/conda_envs \
PIP_CACHE_DIR=/root/autodl-tmp/pip_cache \
ACTION=create bash scripts/prepare_official_baseline_envs.sh o_lora
```

- This avoids placing the new conda env and pip wheel cache on the nearly full root partition. The previously created partial `/root/miniconda3/envs/lora_v10_o_lora` still exists and should be removed only after confirming it is unused.

Cleanup:

- Confirmed the root-partition `lora_v10_o_lora` env was the failed partial created by this repair attempt.
- Removed it with `conda env remove -y -n lora_v10_o_lora`, reducing root partition usage from 99% to 91%.
- The active retry uses `/root/autodl-tmp/conda_envs/lora_v10_o_lora` and `/root/autodl-tmp/pip_cache`, so the cleanup does not affect the retry or any experiment outputs.

### O-LoRA Env Compatibility Fix - 2026-06-19 03:33 CST

- The `/root/autodl-tmp` O-LoRA env successfully installed the official requirements, but `src/run_uie_lora.py --help` failed because `datasets==1.17.0` pulled a too-new `pyarrow` first, and then `pyarrow==12.0.1` was ABI-incompatible with `numpy==2.0.2`.
- Updated `scripts/prepare_official_baseline_envs.sh` to pin both `numpy<2` and `pyarrow<13` for O-LoRA before the help smoke.
- Started an in-place repair on `/root/autodl-tmp/conda_envs/lora_v10_o_lora`; wait for `O_LORA_NUMPY_FIX_DONE` or `O_LORA_NUMPY_FIX_FAILED`.
- `O_LORA_NUMPY_FIX_FAILED` exposed the next legacy dependency issue: `deepspeed==0.8.3` is incompatible with `pydantic>=2`.
- Updated the O-LoRA env script again to pin `pydantic<2` together with `numpy<2` and `pyarrow<13`.
- Started another in-place repair; wait for `O_LORA_PYDANTIC_FIX_DONE` or `O_LORA_PYDANTIC_FIX_FAILED`.
- `O_LORA_PYDANTIC_FIX_DONE`: O-LoRA official env now passes `src/run_uie_lora.py --help`; output is saved at `/tmp/lora_v10_o_lora_help.txt`.
- Updated `results/tables/lora_run_v10_strict_alignment_tracker.csv`: O-LoRA cells for InstrDialog, InstrDialog++, TRACE, MultiWOZ NLG, and Seq-GLUE moved from `scaffold-not-strict` to `official-env-smoke-passed`. They still require a v10 runner bridge plus benchmark data/metric mapping before full strict runs.

### O-LoRA Seq-GLUE Bridge Smoke - 2026-06-19 04:15 CST

- Added `scripts/export_seqglue_to_olora.py`, a no-training exporter from `data/processed/seqglue_cl_tasks_train50_eval10.json` to the official O-LoRA UIE layout.
- Export output: `data/olora/seqglue_s123/`, including `data/`, `task_configs/{train,dev,test}_tasks.json`, `instruction_config_cl.json`, and `manifest.json`.
- CPU no-train smoke passed with the official O-LoRA runner using:
  - `--data_dir data/olora/seqglue_s123/data`
  - `--task_config_dir data/olora/seqglue_s123/task_configs`
  - `--instruction_file data/olora/seqglue_s123/instruction_config_cl.json`
  - `--do_train false --do_eval false --do_predict false --no_cuda true`
- Updated `results/tables/lora_run_v10_strict_alignment_tracker.csv`: `O-LoRA / Seq-GLUE` moved to `runner-bridge-smoke-passed`.
- Remaining step before strict result: queue a full official O-LoRA Seq-GLUE single-seed GPU run after the active LFPT5 run releases CUDA, then compare against the published O-LoRA paper metrics.

### User-Requested Stop and Strict Prep - 2026-06-19 10:05 CST

User instruction changed the execution policy: stop the active LFPT5 / Seq-GLUE `fix3` partial run immediately, preserve all artifacts, then prepare strict published-paper reproduction settings for the full matrix.

Stopped partial:

- Stopped tmux/processes for `lora_run_v10_seqglue_lfpt5_s123_fix3` at 2026-06-19T10:00:15+08:00 by sending Ctrl-C to tmux `lora_run_v10_seqglue_lfpt5_fix3` and SIGTERM to remaining fix3 processes.
- Preserved run dir `results/runs/lora_run_v10_seqglue_lfpt5_s123_fix3/`, log `results/logs/lora_run_v10/lora_run_v10_seqglue_lfpt5_s123_fix3.log`, and W&B run `fc8g2yup`.
- Partial metrics remain exactly as written: `glue_sst2=1.0`, `glue_mrpc=0.8`, `glue_rte=0.6`, `glue_cola=0.5`; the log had entered `super_glue_boolq` but no boolq metric row was written.
- Tracker status for `LFPT5 / Seq-GLUE` is now `user-stopped-partial`; this is not a completed strict full run.

Started strict full run:

- Started `LFPT5 / InstrDialog++ / seed 123` clean rerun in tmux `lora_run_v10_instrdialogpp_lfpt5_clean` at 2026-06-19 10:00 CST.
- Command: `WANDB_PROJECT=lora-run_v10 WANDB_GROUP=lora-run_v10 WANDB_MODE=online python scripts/run_lfpt5_published_setting.py --config configs/paper/published_setting/instrdialogpp__lfpt5__s123.yaml`.
- Run dir: `results/runs/published_instrdialogpp_lfpt5_s123/`.
- Log: `results/logs/lora_run_v10/published_instrdialogpp_lfpt5_s123_clean.log`.
- W&B: project `lora-run_v10`, group `lora-run_v10`, run id `jvp9lun8`.
- Startup reached segment 0 `task1549_wiqa_answer_generation_missing_step`; tracker and gap manifest/status are now `running`.

Strict settings / blockers by method:

- Sequential LoRA: published-setting configs and data exist for InstrDialog, InstrDialog++, TRACE, MultiWOZ NLG, and Seq-GLUE. Not directly strict yet because backbone, LoRA rank/alpha/dropout, optimizer, task order, and metric protocol still need paper audit before a v10 full run. TOD37 remains data-blocked.
- Replay LoRA: configs/data exist for the same non-TOD37 benchmarks. Not directly strict yet because official replay memory size, sampling rule, update timing, and metric protocol still need audit. TOD37 remains data-blocked.
- O-LoRA: official source and env at `/root/autodl-tmp/conda_envs/lora_v10_o_lora` are usable. Seq-GLUE now has `configs/paper/lora_run_v10/seqglue__o_lora_official__s123.yaml` and `scripts/run_olora_seqglue_official.py`; dry-run passed and printed the full official command. It is ready for the next GPU slot after LFPT5 InstrDialog++ finishes. Other benchmarks still need official data mapping/runner bridges. TOD37 remains data-blocked.
- LB-CL: no dedicated official source is present locally. Added a faithful port design to `docs/lora_run_v10_official_baseline_integration.md`; all LB-CL non-TOD37 rows are now `faithful-port-required`, and TOD37 is additionally data-blocked.
- Progressive Prompts: official source exists and env check commands are prepared, but the v10 path still lacks a real trainable soft-prompt/progressive composition runner bridge. Not directly startable as strict.
- Continual-T0: official source exists and env setup command is prepared, but strict runs need T0/T5 checkpoint, official task mixture/templates, rehearsal data/percentage, and runner bridge. Not directly startable as strict.
- LFPT5: InstrDialog++ is currently the active strict full run. InstrDialog, TRACE, and MultiWOZ NLG have old reference outputs only and need v10 rerun/audit under the fixed bridge. Seq-GLUE fix3 is partial by user stop. TOD37 remains data-blocked.
- Ours: available as project-method comparison configs, not a baseline-paper reproduction. Needs separate v10 audit/rerun for our table; TOD37 remains data-blocked.

Tracker updates:

- `results/tables/lora_run_v10_strict_alignment_tracker.csv`: updated LFPT5 Seq-GLUE, LFPT5 InstrDialog++, O-LoRA Seq-GLUE, and LB-CL rows.
- `results/tables/published_setting_run_v2_gap_manifest.csv` and `results/tables/published_setting_run_v2_gap_status.csv`: `published_instrdialogpp_lfpt5_s123` marked `running` with the clean v10 log path and W&B run id.

## Ordered Strict Alignment Audit - 2026-06-19 10:45 CST

User correction: the tracker/plan/queue must follow the requested Method order first, then Benchmark order, rather than the earlier GPU/P0-oriented LFPT5-first queue.

Required order from now on:

1. Sequential LoRA: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
2. Replay LoRA: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
3. O-LoRA: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
4. LB-CL: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
5. Progressive Prompts: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
6. Continual-T0: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
7. LFPT5: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.
8. Ours: InstrDialog -> InstrDialog++ -> TRACE -> MultiWOZ NLG -> Seq-GLUE or TOD37.

Why the current running job exists:

- At 2026-06-19 10:00 CST, the execution policy was changed to stop the active LFPT5 / Seq-GLUE `fix3` partial and start a clean LFPT5 / InstrDialog++ run. That action followed the previous LFPT5-first GPU/P0 plan, not the Method-first ordering above.
- Current active tmux session: `lora_run_v10_instrdialogpp_lfpt5_clean`.
- Current command:

```bash
cd /root/autodl-tmp/Lora-code && WANDB_PROJECT=lora-run_v10 WANDB_GROUP=lora-run_v10 WANDB_MODE=online python scripts/run_lfpt5_published_setting.py --config configs/paper/published_setting/instrdialogpp__lfpt5__s123.yaml 2>&1 | tee -a results/logs/lora_run_v10/published_instrdialogpp_lfpt5_s123_clean.log
```

- Current evidence: tmux/processes are active; CUDA 0 is owned by `external_baselines/lfpt5/citb_bridge/run_continual.py`; W&B run is `jvp9lun8` in project/group `lora-run_v10`; `run_manifest.json` records LM-adapted T5-large checkpoint readiness, 38 segments, and bridge `--max-epoch 4 --cuda 0`; log reached segment 13 by 10:47 CST.
- Strict setting status: `running-needs-setting-verification`, not certified strict. The config proves seed 123, InstrDialog++ train50/eval10, LM-adapted T5-large checkpoint, prompt number 300, batch size 2, and W&B `lora-run_v10`, but it does not yet cite/prove optimizer/lr, `max_epoch=4`, evaluation scoring, and InstrDialog++ protocol against the published LFPT5 setting. Early metrics are also all zero, so no strict result should be claimed before audit and comparison.
- Decision: do not stop it without a user stop command. Let it continue while the setting audit runs. If the paper-setting audit later shows it is not aligned, recommend stop/archive/restart rather than silently using the output.

Strictly verified cells:

- None are currently certified as strict published-paper reproductions across the full requested checklist: backbone, LoRA rank/alpha/dropout when applicable, optimizer/lr, batch/epoch/steps, task order, data split, metric, evaluation protocol, single seed, W&B group `lora-run_v10`, and tmux execution.
- `O-LoRA / Seq-GLUE` has a dry-run official runner bridge and exported data, but it is not in the current user-order position and still needs full paper-setting verification before any strict claim.
- LFPT5 / InstrDialog++ is running with some required evidence, but remains `running-needs-setting-verification`.

Cells that cannot start full runs now:

- Any `needs-paper-setting-audit` row cannot start until the checklist is complete and a v10 config/command is written.
- All TOD37 rows remain blocked by missing TM19/TM20/SGD preprocessing/data.
- O-LoRA, Progressive Prompts, and Continual-T0 unified entries remain scaffold paths unless their official runners/bridges are used and audited.
- LB-CL cannot start a strict run until official code is obtained or a faithful port is implemented and audited.
- No new GPU full run should be launched while LFPT5 / InstrDialog++ owns CUDA 0.

First ordered cell startup checklist: Sequential LoRA / InstrDialog.

- Config exists: `configs/paper/published_setting/instrdialog__sequential_lora__s123.yaml`.
- Data stream exists by prior smoke: `data/processed/citb_cl_dialogue_tasks_train50_eval10.json`.
- Current config values found: Llama-3.1-8B-Instruct, LoRA `r=16`, `alpha=32`, `dropout=0.05`, target modules `q_proj`/`v_proj`, epochs per segment `1`, batch size `2`, lr `0.0002`, seed `123`, train50/eval10, full segment stream.
- Blocking gaps: no local audit yet proves those values match the published baseline paper; current W&B project/group still point to `lora-published-setting-run_v2` / `published_setting_instrdialog`, not `lora-run_v10`; exact optimizer implementation, scheduler, metric/evaluation protocol, and paper task-order citation still need verification.
- Result: do not launch. The first action is a no-GPU paper-setting audit and v10 config rewrite. If and only if the checklist passes and CUDA 0 is free, use a tmux command in this shape:

```bash
tmux new-session -d -s lora_run_v10_instrdialog_sequential_lora \
  'cd /root/autodl-tmp/Lora-code && WANDB_PROJECT=lora-run_v10 WANDB_GROUP=lora-run_v10 WANDB_MODE=online python core/train.py --config configs/paper/lora_run_v10/instrdialog__sequential_lora__s123.yaml 2>&1 | tee -a results/logs/lora_run_v10/lora_run_v10_instrdialog_sequential_lora_s123.log'
```

Tracker update:

- `results/tables/lora_run_v10_strict_alignment_tracker.csv` now uses `Mxx-Bxx` priorities that encode the user-requested Method -> Benchmark order.
- All cells without proof are marked `needs-paper-setting-audit` or an explicit blocked/running variant of that state. No row should be reported as strict until the full checklist is documented.

## Strict Paper-Setting Checklist Pass - 2026-06-19 10:55 CST

Execution boundary respected:

- No new full run was launched.
- No running process was stopped.
- No data or result artifact was deleted.

Checklist document added:

- `docs/lora_run_v10_strict_paper_setting_checklist.md` is now the strict paper-setting gate for the requested matrix. It records, per method, the published source/path, implementation path, backbone, adapter or prompt parameters, optimizer/lr/batch/epoch/step evidence, task order, split/data path, metric/eval protocol, seed, W&B/tmux readiness, and status.
- For code/config-confirmed items the document lists evidence. For unconfirmed items it explicitly uses `needs-paper-setting-audit`, `official-source-needs-bridge-and-paper-audit`, `faithful-port-required`, or `blocked-data-*`.

Tracker corrections:

- `LFPT5 / InstrDialog++` remains `running-needs-setting-verification`. The active tmux session `lora_run_v10_instrdialogpp_lfpt5_clean` uses `configs/paper/published_setting/instrdialogpp__lfpt5__s123.yaml`; it proves seed 123, LM-adapted T5-large, prompt number 300, batch size 2, train50/eval10, and W&B `lora-run_v10`, but it still lacks a completed LFPT5 paper-setting audit for optimizer/lr, `--max-epoch 4`, scoring, and InstrDialog++ protocol. Do not call it strict-complete.
- `O-LoRA / Seq-GLUE` is now `runner-bridge-smoke-passed-needs-paper-setting-audit`: official env, data bridge, and dry-run wrapper exist, but the published-paper backbone/hparams/eval checklist is not complete and the Method-order queue has not reached this cell.
- `LB-CL` non-TOD37 cells are now `faithful-port-required`; TOD37 is `blocked-data-and-faithful-port-required`. No dedicated official source exists locally, so a strict LB-CL full run is blocked until official code is obtained or a faithful sensitivity/projection/triplet port is implemented and audited.
- `Progressive Prompts` and `Continual-T0` rows now explicitly say official source exists but runner bridge, dependency/runtime, and paper protocol audit are incomplete. TOD37 rows also retain the data blocker.

Current running-task recommendation:

- Keep `LFPT5 / InstrDialog++` running only as `running-needs-setting-verification` unless the user chooses to stop it. If the LFPT5 audit fails or the metrics remain suspicious, the recommended action is to stop/archive/restart with corrected settings rather than use the output as a strict result.

Remaining blockers:

- Sequential LoRA and Replay LoRA need paper-protocol audit before any full run; current published-setting YAMLs are evidence inputs, not strict certification.
- O-LoRA has official Seq-GLUE bridge readiness, but still needs strict paper-setting audit before full run.
- LB-CL lacks dedicated official source.
- Progressive Prompts and Continual-T0 need official runner bridges, dependency readiness, and paper hparam/protocol audits.
- TOD37 still lacks TM19, TM20, and SGD raw data plus AdapterCL/ToDCL preprocessing/export into the v10 stream.

## Strict Paper-Setting Continuation - 2026-06-19 11:27 CST

Execution boundary respected:

- No new full run was launched.
- No running process was stopped.
- No data, checkpoint, or result artifact was deleted.
- Proxy config `/root/autodl-tmp/Lora-code/configs/clash` was noted for future external downloads, but this pass used only local repo/config/run evidence and did not access external sources.

Sequential LoRA / InstrDialog audit:

- Config evidence exists at `configs/paper/published_setting/instrdialog__sequential_lora__s123.yaml`: Llama-3.1-8B-Instruct, LoRA r16/alpha32/dropout0.05 on `q_proj`/`v_proj`, lr 2e-4, batch size 2, one epoch per segment, seed 123, train50/eval10 stream `data/processed/citb_cl_dialogue_tasks_train50_eval10.json`.
- Code evidence: `baselines/basic_baselines/sequential_lora/method.py` uses one default adapter and trains segments sequentially with no replay/bank/router. `core/models/lora_wrapper.py` uses AdamW over LoRA parameters and updates LR from `fit_batch`; no scheduler is present, and the config `grad_clip_norm` is not applied in `step_adapter()`.
- Evaluation evidence: `core/evaluate.py` evaluates all seen segments after each segment and logs exact-match current/seen scores, task-aware scores, forgetting, token F1, LCS, ROUGE-L, BLEU, and slot error when slots are present.
- Blocker: no local paper/source audit proves these backbone, LoRA, optimizer, task order, split, and metric choices match the published baseline. Current config also still points at `lora-published-setting-run_v2`, not `lora-run_v10`.
- Decision: keep `Sequential LoRA / InstrDialog` as `needs-paper-setting-audit`; do not create/promote a runnable v10 full-run config until the published setting is proven or explicitly labelled non-strict.

Replay LoRA / InstrDialog audit:

- Config evidence exists at `configs/paper/published_setting/instrdialog__replay_lora__s123.yaml`: same backbone/LoRA/train stream as Sequential, with replay buffer size 50, replay ratio 0.3, uniform sampling.
- Code evidence: `baselines/basic_baselines/replay_lora/method.py` adds current segment samples to the buffer before mixing, drops oldest samples on overflow, and samples `round(len(current) * replay_ratio)` replay examples uniformly.
- Blocker: official replay memory size, sampling rule, update timing, optimizer/backbone, and metric protocol are not verified. The current implementation may mismatch a paper replay baseline if replay should sample previous tasks only.
- Decision: keep `Replay LoRA / InstrDialog` as `needs-paper-setting-audit`, lower priority than completing the Sequential LoRA method block.

LFPT5 / InstrDialog++ running audit:

- tmux `lora_run_v10_instrdialogpp_lfpt5_clean` is active; W&B run is `jvp9lun8` in project/group `lora-run_v10`; `run_manifest.json` records 38 segments, LM-adapted T5-large checkpoint readiness, and bridge `--max-epoch 4 --cuda 0`.
- Current metrics through segment 12 all have `eval.current_score=0.0`; token F1 remains near zero. The live log has reached at least segment 13.
- Bridge defaults are local evidence only: LFPT5 `lr=5e-5`, `kd_lamda=0.05`, `gradient_accumulation_steps=1`, batch size 2, prompt number 300, exact-match/token-F1 scoring. These have not been proven against the LFPT5 published paper setting for InstrDialog++.
- Recommendation: do not stop without a user stop command, but do not use this output as strict. If the goal is strict published-paper alignment, the current evidence supports stop/archive/restart after the LFPT5 setting audit rather than accepting a zero-score run.

Tracker/checklist updates:

- `docs/lora_run_v10_strict_paper_setting_checklist.md` updated with the above code/runtime evidence.
- `results/tables/lora_run_v10_strict_alignment_tracker.csv` updated for `Sequential LoRA / InstrDialog`, `Replay LoRA / InstrDialog`, and `LFPT5 / InstrDialog++`.
- O-LoRA Seq-GLUE, LB-CL, Progressive Prompts, Continual-T0, and TOD37 remain blocked or audit-only exactly as recorded in the strict checklist/tracker; no training was started for them.

## Strict Paper-Setting Continuation - 2026-06-19 22:00 CST

Execution boundary respected:

- No new full run was launched.
- No running process was stopped.
- No data, checkpoint, or result artifact was deleted.
- Proxy config exists under `configs/clash` with HTTP/SOCKS ports `7890`/`7891`, but no local proxy listener was found during this pass. External source lookup used available search results rather than starting proxy services.

Run/GPU state:

- No active `lora_run_v10_instrdialogpp_lfpt5_clean` tmux session was found in the current `tmux ls`.
- CUDA 0 was idle at the start of this pass.
- Existing monitor/supervisor tmux sessions remain, but no new full-run tmux was started.

Sequential LoRA / InstrDialog strict checklist:

- Published source found for the benchmark/protocol: CITB: A Benchmark for Continual Instruction Tuning (EMNLP Findings 2023 / OpenReview) defines InstrDialog/InstrDialog++, sequential single-task fine-tuning, Replay, task streams, splits, and AR/FWT/BWT/FR reporting.
- Local config/code evidence remains: `configs/paper/published_setting/instrdialog__sequential_lora__s123.yaml` uses Llama-3.1-8B-Instruct, LoRA r16/alpha32/dropout0.05 on `q_proj`/`v_proj`, lr 2e-4, batch size 2, one epoch per segment, seed 123, train50/eval10 stream `data/processed/citb_cl_dialogue_tasks_train50_eval10.json`; `baselines/basic_baselines/sequential_lora/method.py` trains one default adapter sequentially; `core/models/lora_wrapper.py` uses AdamW over LoRA params and no scheduler.
- Strict blocker is now explicit, not merely unknown: CITB's InstrDialog setting uses LM-adapted T5-small with an initial instruction-tuned model, full fine-tuning baselines (`FT-init`/`FT-no-init`) rather than LoRA, InstrDialog 500/50/100 train/dev/test rather than local train50/eval10, and AR/FWT/BWT/FR over stream/init/unseen sets rather than the local exact-match/token-F1 table.
- Decision: `Sequential LoRA / InstrDialog` is now `blocked-paper-mismatch`. Do not launch a strict run. The minimum blocker is deciding whether to implement the CITB T5/full-finetune protocol for this cell or explicitly relabel the local Llama LoRA run as a non-strict adaptation.

Replay LoRA / InstrDialog side audit:

- CITB source verifies Replay (10)/(50): random memory instances per task, jointly trained with `M_init`, `M_seq`, and new task data.
- Local replay config/code uses Llama LoRA, buffer size 50, ratio 0.3, uniform sampling, adds current-segment samples before replay mixing, drops oldest overflow, and does not implement `M_init` memory.
- Decision: `Replay LoRA / InstrDialog` is also `blocked-paper-mismatch`, but remains lower priority than resolving the first ordered Sequential LoRA cell.

LFPT5 / InstrDialog++ status:

- The previously active clean run has completed and written `results/runs/published_instrdialogpp_lfpt5_s123/final_metrics.json`, `results/tables/published_instrdialogpp_lfpt5_s123_segment_metrics.csv`, and W&B run `jvp9lun8`.
- The result is not strict: all 38 segment rows have zero exact-match/task-aware scores; final `eval.current_score=0.0`, `eval.seen_avg_score=0.0`, and `eval.token_f1_mean=0.0020266388509749445`.
- Recommendation: preserve it as diagnostic output only. Do not use it as a strict published-paper result; if revisited, audit LFPT5 paper hyperparameters/scoring first and rerun with corrected settings.

Tracker/checklist updates:

- `docs/lora_run_v10_strict_paper_setting_checklist.md` updated with CITB source evidence, explicit Sequential/Replay mismatch blockers, and the completed-but-non-strict LFPT5 InstrDialog++ result.
- `results/tables/lora_run_v10_strict_alignment_tracker.csv` updated for `Sequential LoRA / InstrDialog`, `Replay LoRA / InstrDialog`, and `LFPT5 / InstrDialog++`.

## Strict Alignment Evidence Pass - 2026-06-19 22:55 CST

Execution boundary respected:

- No new full run was launched.
- No running training or monitor process was stopped.
- No data, checkpoint, or result artifact was deleted.

Evidence-chain updates:

- `scripts/check_lora_run_v10_strict_alignment.py` now writes `results/tables/lora_run_v10_strict_alignment_evidence.json` in addition to the summary JSON and markdown report. The evidence file records per-cell strict gates for official/paper source, paper hparams, data processing, label/instruction mapping, metric protocol, official/equivalent runner, full-run/equivalent evidence, and `strict_allowed`.
- Generated matrix result: 48 / 48 cells covered, 0 strict-allowed cells, no validation errors.
- `scripts/export_seqglue_to_olora.py --validate-only` now checks the expected 8 Seq-GLUE segment order, 50/10 train/eval counts, per-split task config coverage, label files, non-empty splits, and sampled example schema/label membership.

Validation commands and outcomes:

```bash
python -m py_compile scripts/check_lora_run_v10_strict_alignment.py scripts/export_seqglue_to_olora.py scripts/run_olora_seqglue_official.py
python scripts/export_seqglue_to_olora.py --out-root data/olora/seqglue_s123 --validate-only
python scripts/run_olora_seqglue_official.py --dry-run
python scripts/check_lora_run_v10_strict_alignment.py
```

- Result: all commands above passed.
- `python scripts/convert_tod37_to_stream.py --check-only` was also run and returned exit code 2 as expected because TOD37 raw data is still missing. The blocker manifest lists TM19, TM20, SGD train/dev/test, and MultiWOZ 2.2 raw paths.

Current strict conclusion:

- Strict-complete remains empty. O-LoRA / Seq-GLUE is runner-ready but still lacks full official run and paper metric/hparam audit. LFPT5 / InstrDialog++ is completed diagnostic output only because all exact-match/task-aware scores are zero and hparam/scoring protocol is not paper-proven. LFPT5 / Seq-GLUE remains user-stopped partial. All remaining cells are blocked by paper mismatch, missing official bridge/source, missing faithful port, project-method comparison audit, or TOD37 data.
