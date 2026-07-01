# SOTA Optimization Campaign — Status

**Campaign started**: 2026-06-24  
**Repo**: `/root/autodl-tmp/Lora-code`  
**Tracker**: [SOTA_GAP_TRACKER.md](./SOTA_GAP_TRACKER.md)

## Version lineage

| Version | Path | Git @ snapshot | Description |
|---------|------|----------------|-------------|
| **v0_baseline** | `experiments/sota_campaign/v0_baseline/` | `d711d912926c` | Pre-campaign snapshot (causal-only backbone in Lora-code; strict runs used `Lora-Baselines/.../project_local`) |
| **v1_citb_kalman_drift** | `experiments/sota_campaign/v1_citb_kalman_drift/` | `d711d912926c` + local patches | CITB T5 prompt alignment + seq2seq backbone port + Kalman-smoothed drift NLL |

## v0 — baseline audit

### Root cause: CITB strict AR ≈ 0.013

Evidence from `citb_instrdialog_order1_seed1_ours_strict`:

- `eval_debug` shows `raw_generated_output: "."` and `bad_prefix_mismatch: true` on classification tasks
- Prompt uses Llama-style *"You must answer as concisely..."* constraint; **CITB Stage-1 T5 was trained with SuperNI `Definition: … / Input: … / Output:` format**
- `Lora-code` lacked `seq2seq_lm` backbone routing (strict runs used symlinked `project_local` copy)
- LoRA PEFT task type was hardcoded `CAUSAL_LM` in `Lora-code` (running job uses `SEQ_2_SEQ_LM` via `project_local`)

### Non-blocking observations

- Drift detector fires frequently (probe CUSUM); branch count grows to 6 by seg 18
- Router oracle agreement drops to ~19% late in stream (routing quality concern for v2+)
- FWT / T_init / T_unseen not emitted in strict metrics.jsonl

## v1 — `citb_kalman_drift` (incremental, novel)

### A) Blocking fixes (eval / training alignment)

1. **Port `HFSeq2SeqLMBackbone`** (`core/models/seq2seq_lora_wrapper.py`) + route `task_type: seq2seq_lm` in `build_hf_backbone`
2. **CITB T5 prompt formatting** (`format_citb_t5` in `core/formatting.py`) — matches official `ni_collator` (`Definition` + `Now complete the following example`)
3. **Auto format style** for T5 tokenizers; explicit `model.format_style: citb_t5` in configs
4. **PEFT `SEQ_2_SEQ_LM`** task type resolution in `LoRAWrapper`

### B) Novel algorithm increment — Kalman-smoothed anchor NLL drift gate

**Config flags** (`drift:` block):

```yaml
kalman_drift_enabled: true
kalman_process_var: 0.02
kalman_measure_var: 0.25
```

**Mechanism**: Before CUSUM on core/probe anchor NLL, apply a 1D Kalman filter to estimate latent drift state from noisy batch observations. Reduces false-positive branch spawns from NLL spikes without using task boundaries.

**Novelty claim** (vs searchable literature):

- Kalman filtering for CL appears mainly for **weight-space** tracking (EKF on parameters; DeepMind ICLR 2024 OCL) or **non-stationary classification**, not for **task-free LoRA bank boundary detection via anchor NLL**
- Our stack combines: anchor-set NLL monitoring (existing) + CUSUM (existing) + **Kalman observation smoothing (new)** in a PEFT continual LoRA router system
- Distinct from Kalman Optimiser (Fisher-grouped long/short memory) and from supervised task-boundary HMMs

**Incremental rationale**: Single scalar filter per anchor tier; default off; no change to bank/router/anti-overlap when disabled.

## Implementation status (updated 2026-06-24 06:10 CST)

| Item | Status |
|------|--------|
| overlap_loss device bug (CUDA/CPU) | ✅ fixed in `Lora-code/core/methods/overlap_loss.py` |
| CCFA postprocess / ROUGE-L AR wire-up | ✅ `core/ccfa_metrics.py` + `train.py` |
| v1.1 archive `v1_1_ccir_router_kl/` | ✅ `meta.json` + CCIR configs |
| order1 v1 strict rerun (post-fix) | 🔄 launch via `launch_order1_v1_rerun.sh` (GPU was idle; `sota_loop` paused) |
| order2 / order3 v1 | ❌ crashed pre-fix at first drift spawn (seg 5 / seg 2) |

### Version lineage (updated)

| Version | Path | Description |
|---------|------|-------------|
| **v1_citb_kalman_drift** | `experiments/sota_campaign/v1_citb_kalman_drift/` | CITB T5 + Kalman drift + device-fix snapshot |
| **v1_1_ccir_router_kl** | `experiments/sota_campaign/v1_1_ccir_router_kl/` | v1 + CCIR routing bundle + matched-KL orthogonal reg |

### Blocking bug fix

**Root cause**: `HFSeq2SeqLMBackbone.get_activations_tensor(with_grad=False)` moves pooled activations to CPU; active branch stays on CUDA when `b1` spawns → `overlap_loss.py` mixed-device crash.

**Fix**: align all branch activation/weight tensors to model device in `compute_overlap_loss_torch` / `compute_anti_overlap_training_loss`.

### Rerun commands

```bash
# Pause loop (if running) and start order1 with fix
bash /root/autodl-tmp/Lora-code/experiments/sota_campaign/launch_order1_v1_rerun.sh
tail -f /root/autodl-tmp/Lora-code/experiments/sota_campaign/logs/citb_instrdialog_order1_seed1_ours_v1_strict_rerun.nohup.log

# Resume loop after rerun
rm /root/autodl-tmp/Lora-code/experiments/sota_campaign/PAUSE_SOTA_ITERATION_LOOP
```

---

## Implementation status (2026-06-24)

| Item | Status |
|------|--------|
| v0 archive | ✅ |
| v1 code in `Lora-code/core/` | ✅ |
| v1 snapshot in `v1_citb_kalman_drift/` | ✅ |
| Smoke config | ✅ `v1_citb_kalman_drift/configs/citb_instrdialog_smoke_v1.yaml` |
| Smoke run | 🔄 `citb_instrdialog_smoke_v1` (PID train ~637492) |

## Next steps

1. After order2 finishes, run v1 smoke (1 segment) on free GPU
2. If ROUGE-L AR @ seg0 ≫ 0, launch `citb_instrdialog_order1_seed1_ours_v1_strict` full rerun
3. Wire CITB `T_init` / `T_unseen` / FWT aggregation in postprocess
4. v2 candidate: router calibration via probe-NLL arbitration (address 19% oracle agreement)

## Smoke / full run commands

```bash
# Smoke (1 segment, v1) — run when GPU free
cd /root/autodl-tmp/Lora-code
python core/train.py --config experiments/sota_campaign/v1_citb_kalman_drift/configs/citb_instrdialog_smoke_v1.yaml

# Full strict rerun (draft — copy ccfa config + add model.format_style + drift.kalman_*)
# python core/train.py --config /root/autodl-tmp/lora-baselines-run_v1/configs/ccfa_three_suite/citb_instrdialog_order1_seed1_ours_v1_strict.yaml
```

## GPU takeover & launch (2026-06-24 03:42 CST)

User authorized **stop old CCFA strict jobs** and **start SOTA v1** on single-GPU serial queue.

### Stopped processes

| PID | Process | Notes |
|-----|---------|-------|
| 491989 | `python core/train.py` … `citb_instrdialog_order2_seed2_ours_strict.yaml` | SIGTERM → exited; was using ~12818 MiB GPU |
| 318959 | `run_ccfa_strict_sequential_recovery_queue.sh` | SIGTERM |
| 321750, 321752 | `run_ccfa_experiment_supervisor_loop.sh loop` | SIGTERM (321753 tee exited with parent) |

- Stop log: `experiments/sota_campaign/logs/process_stop_20260624_034154.log`
- CCFA recovery paused: `lora-baselines-run_v1/status/PAUSE_CCFA_RECOVERY_QUEUE`
- Removed campaign pause flag: `experiments/sota_campaign/PAUSE_SOTA_V1`

### Active SOTA run

| Role | PID | Command / artifact |
|------|-----|-------------------|
| Serial queue driver | **637482** | `experiments/sota_campaign/run_sota_v1_citb_serial.sh` |
| Current train | **637492** (smoke; may change as queue advances) | `python core/train.py --config …/citb_instrdialog_smoke_v1.yaml` |

**Logs**

- Queue meta: `experiments/sota_campaign/logs/sota_v1_citb_serial_queue.log`
- Queue nohup: `experiments/sota_campaign/logs/sota_v1_citb_serial_queue.nohup.log`
- Smoke train: `experiments/sota_campaign/logs/citb_instrdialog_smoke_v1.nohup.log`

### Serial queue (after smoke succeeds)

1. ✅ **Running** — `citb_instrdialog_smoke_v1.yaml` (1 segment)
2. ⏳ **Queued** — ``citb_instrdialog_order1_seed1_ours_v1_strict.yaml`
3. ⏳ **Queued** — `citb_instrdialog_order2_seed2_ours_v1_strict.yaml`
4. ⏳ **Queued** — `citb_instrdialog_order3_seed3_ours_v1_strict.yaml`

Configs: `experiments/sota_campaign/v1_citb_kalman_drift/configs/` (also copied order1 to `lora-baselines-run_v1/configs/ccfa_three_suite/`).

All v1 strict configs include `model.format_style: citb_t5`, `task_type: seq2seq_lm`, `drift.kalman_drift_enabled: true`.

### Implementation status (updated)

| Item | Status |
|------|--------|
| v1 full strict configs (order1–3) | ✅ |
| Stop legacy GPU / recovery | ✅ |
| Smoke run | 🔄 in progress |
| Full order1 v1 strict | ⏳ queued after smoke |

---

## Continuous SOTA loop (2026-06-24 03:51 CST)

### Process stop (user-authorized)

- Stopped `run_sota_v1_citb_serial.sh` (pid ~637482) and GPU `train.py` (pid ~637892, order1 v1 strict, interrupted)
- Stopped `sota_iteration_agent.py` (pid ~359384), `supervisor_published_setting_run_v2.py` (pid ~530444), `monitor_four_benchmark_single_seed.py` (pid ~500585)
- Killed tmux: `sota-monitor`, `v8s5camp_supervisor`, `v8s5camp_agent_loop`, `lora_strict_supervisor`, `lora_strict_agent_loop`
- Log: `logs/process_stop_20260624_034941.log`

### PAUSE flags (prevent legacy restarts)

| Flag | Purpose |
|------|---------|
| `PAUSE_SOTA_V1_SERIAL` | Blocks `run_sota_v1_citb_serial.sh` |
| `PAUSE_SOTA_LEGACY_MONITORS` | Documented guard for old monitor agents |
| `PAUSE_SOTA_V2` / `PAUSE_SOTA_V3` | Legacy paper SOTA tmux launches |
| `lora-baselines-run_v1/status/PAUSE_CCFA_RECOVERY_QUEUE` | CCFA recovery queue |

### Active supervisor

| Item | Value |
|------|-------|
| tmux session | **`sota_loop`** |
| Launcher | `experiments/sota_campaign/start_sota_loop_tmux.sh` |
| Loop script | `experiments/sota_campaign/run_sota_iteration_loop.sh` |
| Version | `v1_citb_kalman_drift` |
| wandb project | **`ours-sota-campaign`** (`use_wandb: true` in v1 configs) |
| Current run | **`citb_instrdialog_order1_seed1_ours_v1_strict`** (smoke skipped — already done) |
| Gap tool | `experiments/sota_campaign/sota_gap_check.py` |

### Monitor

```bash
tmux attach -t sota_loop
tail -f /root/autodl-tmp/Lora-code/experiments/sota_campaign/logs/sota_iteration_loop.log
tail -f /root/autodl-tmp/Lora-code/experiments/sota_campaign/logs/citb_instrdialog_order1_seed1_ours_v1_strict.nohup.log
```

**wandb**: `wandb status` shows no local API key in settings; `~/.netrc` has `api.wandb.ai` — runs use `use_wandb: true`; verify dashboard at wandb.ai project `ours-sota-campaign`.

### Pause new loop

```bash
touch /root/autodl-tmp/Lora-code/experiments/sota_campaign/PAUSE_SOTA_ITERATION_LOOP
```
