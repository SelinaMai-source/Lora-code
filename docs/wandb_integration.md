# Weights & Biases (W&B) 接入说明

本仓库通过 `core/wandb_tracker.py` 与 `core/train.py` 集成 W&B。默认关闭；在 YAML 中开启即可。

## 1. 安装与登录

```bash
pip install wandb
wandb login
# 或 export WANDB_API_KEY=your_key
```

## 2. 在配置中开启

将 `configs/tracking_wandb.example.yaml` 中的 `output.tracking` 块复制到你的实验 YAML，或直接在 paper config 里设置：

```yaml
output:
  tracking:
    use_wandb: true
    wandb_project: lora-citb
    wandb_entity: ""              # 可选：团队/用户名
    wandb_group: paper_instrdialog
    wandb_tags: [ours, instrdialog, seed123]
    wandb_mode: online            # online | offline | disabled
    log_artifacts: true
```

也可用环境变量覆盖：

- `WANDB_PROJECT`
- `WANDB_ENTITY`
- `WANDB_MODE=offline`（无网络时本地记录，之后 `wandb sync`）

## 3. 单次运行

```bash
python core/train.py --config configs/paper/instrdialog__ours_no_overlap__s123.yaml
```

在 config 里设 `output.tracking.use_wandb: true` 后，会自动记录：

- 完整 YAML config
- 每个 segment 的 train/eval/drift/router 指标（`wandb.log`，step=segment_id）
- 最终 `final`、`drift_quality`、`routing_quality` 汇总
- 可选 artifact：`metrics.json`、`segment_metrics.csv`、`config_snapshot.yaml`

## 4. 批量 paper matrix + W&B

```bash
bash scripts/run_publication_with_wandb.sh \
  --benchmarks instrdialog \
  --categories main \
  --skip-existing
```

等价于对 matrix 中每条 run 注入：

```text
output.tracking.use_wandb=true
output.tracking.wandb_project=lora-citb
output.tracking.wandb_mode=online
```

也可用 `--set` 单独覆盖，例如：

```bash
python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --set output.tracking.use_wandb=true \
  --set output.tracking.wandb_group=ablation_routed
```

## 5. 投稿向推荐实验顺序

1. **主方法**：`ours_full`，anti-overlap 作为 ACL/ARR 主实验，不再把 `ours_no_overlap` 作为 winner。
2. **Anti-overlap sweep**：优先跑 `ours_beta001 / ours_beta003 / ours_beta006`，确认 curriculum warmup 后的稳定区间。
3. **闭环 routing**：主配置使用 `router.training_strategy=learned_router`，并记录 routed-training 与 router-head orthogonality 指标。
4. **Change-point ablation**：比较 `meta_threshold_enabled=true/false` 与 `curriculum_strategy` 变体。
5. **多 seed**：同一 variant 跑 seed 123/456/789，W&B 用 `wandb_group` 对齐。

## 6. 离线 / CI

```bash
export WANDB_MODE=offline
python core/train.py --config configs/seq_debug.yaml
# 运行结束后
wandb sync wandb/offline-run-*
```

禁用 W&B：`use_wandb: false` 或 `WANDB_MODE=disabled`。
