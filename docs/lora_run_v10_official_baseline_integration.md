# lora-run_v10 Official Baseline Integration Checklist

Updated: 2026-06-19 00:38 CST

This file prevents scaffold outputs from being promoted as strict published-paper reproductions. The unified `baselines/advanced_baselines/*` implementations are useful smoke scaffolds, but strict rows require the official code path or a faithful port with matching data, model, hyperparameters, and metrics.

## Current Inventory

| Method | Official/local source found | Unified entry status | Strict blocker |
| --- | --- | --- | --- |
| O-LoRA | `external_baselines/o_lora`; TRACE/RCL also has `model/Regular/O_LoRA.py` | `baselines/advanced_baselines/o_lora/method.py` is scaffold with orthogonal hooks | Need bind official training/inference entry, task configs, backbone, LoRA targets, and metric protocol before rerun |
| LB-CL | No dedicated official LB-CL source directory found under `external_baselines/` | `baselines/advanced_baselines/lb_cl/method.py` is scaffold with SVD/projection summaries | Need official repository or paper-faithful sensitivity ranking, triplet injection, projection, hparams, and benchmark protocol |
| Progressive Prompts | `external_baselines/progressive_prompts`; TRACE/RCL has `model/Dynamic_network/PP.py` | `baselines/advanced_baselines/progressive_prompts/method.py` is scaffold and has no trainable soft-prompt module | Need official soft-prompt parameter module, progressive prompt concatenation/routing, prompt length/init, and evaluation scripts |
| Continual-T0 | `external_baselines/continual_t0` | `baselines/advanced_baselines/continual_t0/method.py` is instruction replay scaffold only | Need T0/T5 checkpoint, official mixture/templates, rehearsal data/percentage, and paper metrics |

## Required Strict Handoff

1. Add a method-specific runner or bridge under `scripts/` that calls the official source, not the unified scaffold.
2. Pin the official environment in `external_baselines/official_smoke_plan.md` with a smoke command that does not download weights or run full training.
3. Create `configs/paper/lora_run_v10/<benchmark>__<method>__s123.yaml` only after the official task order, backbone, hparams, and metric names are known.
4. Run a CPU/light smoke first, then queue the full single-seed GPU run only when CUDA 0 is free.
5. Update `results/tables/lora_run_v10_strict_alignment_tracker.csv` from `scaffold-not-strict` only after the official path produces a clean v10 result or a documented strict blocker.

## Per-Method Next Actions

- O-LoRA: start from `external_baselines/o_lora/engine.py` and `src/run_uie_lora.py`; resolve hard-coded `/workspace/O-LoRA` paths and official config files before any v10 rerun.
- LB-CL: locate or obtain the official code. If unavailable, write a faithful port design from the paper before implementation; current SVD summary hook is not sufficient.
- Progressive Prompts: start from `external_baselines/progressive_prompts/T5_codebase/t5_continual.py`; map official datasets/prompts to the requested benchmark before claiming strict alignment.
- Continual-T0: start from `external_baselines/continual_t0/README.md`; verify checkpoint/mix/rehearsal assets before running or comparing numbers.

## LB-CL Faithful Port Design

Status: no dedicated official LB-CL source is present under `external_baselines/`. Until official code is obtained, strict LB-CL rows are blocked on a faithful port. The unified `baselines/advanced_baselines/lb_cl/method.py` cannot be used for published-paper reproduction because it only exposes a lightweight SVD/projection scaffold.

Minimum port requirements before any full run:

1. Implement the paper's sensitivity-aware parameter selection rather than a generic projection hook.
2. Reproduce the low-boundary / projection update path, including the triplet or contrastive objective if used by the paper protocol.
3. Pin the exact backbone, LoRA target modules, rank/alpha/dropout, optimizer, scheduler, replay/no-replay setting, task order, and train/eval budget for each requested benchmark.
4. Add a method-specific runner under `scripts/` that writes a run manifest, W&B project/group `lora-run_v10`, and per-segment metrics compatible with the v10 tables.
5. Add a CPU smoke that checks model construction, one synthetic/mini batch, metric formatting, and checkpoint resume without performing a full GPU run.
6. Only then create `configs/paper/lora_run_v10/<benchmark>__lb_cl__s123.yaml` and queue single-seed full runs.

Current blocker wording for tracker rows: "No local official LB-CL source; faithful port required for sensitivity/projection/triplet pipeline and paper hparams before strict full run."

## O-LoRA Seq-GLUE Runner

The official O-LoRA environment and Seq-GLUE data bridge are now runnable without training via:

```bash
python scripts/run_olora_seqglue_official.py --dry-run
```

Full run command for the next free GPU slot:

```bash
tmux new-session -d -s lora_run_v10_seqglue_olora_official \
  'cd /root/autodl-tmp/Lora-code && WANDB_PROJECT=lora-run_v10 WANDB_GROUP=lora-run_v10 WANDB_MODE=online python scripts/run_olora_seqglue_official.py --config configs/paper/lora_run_v10/seqglue__o_lora_official__s123.yaml 2>&1 | tee -a results/logs/lora_run_v10/lora_run_v10_seqglue_o_lora_official_s123.log'
```

Do not start this while another full GPU run owns CUDA 0.
