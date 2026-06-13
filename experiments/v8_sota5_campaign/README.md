# v8_sota5 Paper Campaign

基于冠军配置 `configs/paper/v8_sota_5.yaml` 的独立 W&B 实验战役，与旧项目 `lora-citb-sota` **完全隔离**。

## ours = v8_sota_5 冠军（强制）

本战役中 **ours** 仅指 `configs/paper/v8_sota_5.yaml` 冠军配置，**不是** 旧 paper 矩阵里的 `instrdialog*__ours_full__*.yaml`。

| 项 | 要求 |
|----|------|
| 生成基座 | `configs/paper/v8_sota_5.yaml`（校验 `routing_backend=prototype`、`prototype_update_steps=3`） |
| run_name | `paper_{benchmark}_v8_sota5_ours_s{seed}_v8s5camp` |
| 关键 router | `routing_backend: prototype`, `spawn_sync_prototype_init: true`, `prototype_update_steps: 3` |

## 强制 W&B 记录

```bash
source experiments/v8_sota5_campaign/campaign.env
```

| 变量 | 值 |
|------|-----|
| `WANDB_PROJECT` | `lora-citb-v8-sota5-paper` |
| `WANDB_MODE` | `online` |

## 四阶段执行顺序（单 GPU 串行）

| Phase | 类别 | 内容 | Runs |
|-------|------|------|------|
| **1** | `phase1_priority` | v8_sota_5 ours，seed=123，**仅 instrdialog++** | **1** |
| **2** | `ablation_single_seed` | 5 变体 × 2 benchmarks，seed=123 | **10** |
| **3** | `baseline_multiseed` | 5 baselines × 3 seeds × 2 benchmarks | **30** |
| **4** | `ours_multiseed` | v8_sota_5 × 3 seeds × 2 benchmarks | **6** |

**战役总计：47 runs**

Phase 1 完成后自动调用 `on_run_complete.sh` → `cursor_agent_wake.sh`（中文 metrics 汇报）。

消融变体（Phase 2）：

| variant | 说明 |
|---------|------|
| `v8_sota_5` | 冠军完整配置（= ours） |
| `ours_no_drift` | 关闭 drift detector |
| `ours_no_bank` | 关闭 LoRA bank |
| `ours_no_router` | 关闭 router |
| `ours_no_overlap` | 关闭 overlap loss |

Baselines（Phase 3，**不含** replay_b10）：`seq`, `replay_b50`, `periodic_latest`, `bank_no_router`, `router_only`

## 快速开始

### 1. 生成配置与 manifest

```bash
cd /root/autodl-tmp/Lora-code
python3 experiments/v8_sota5_campaign/generate_configs.py
```

### 2. 加载环境变量

```bash
source experiments/v8_sota5_campaign/campaign.env
```

### 3. 启动 Phase 1（tmux 串行，完成后自动接续 Phase 2–4）

```bash
# 推荐：单 tmux 会话跑完全部四阶段
bash experiments/v8_sota5_campaign/tmux_run_campaign.sh

# 仅 Phase 1（优先任务）
bash experiments/v8_sota5_campaign/tmux_run_campaign.sh 1
```

### 4. 监督系统（建议与训练同时启动）

```bash
# 监控循环
tmux new-session -d -s v8s5camp_supervisor \
  'bash experiments/v8_sota5_campaign/supervisor/monitor_loop.sh'

# Agent 自动唤醒与定期汇报
tmux new-session -d -s v8s5camp_agent_loop \
  'bash experiments/v8_sota5_campaign/supervisor/agent_loop.sh'
```

### 5. 连接 tmux

```bash
tmux attach -t v8s5camp_serial      # 训练进度
tmux attach -t v8s5camp_supervisor   # 健康监控
tmux attach -t v8s5camp_agent_loop   # Agent 唤醒循环
```

### 6. 查看状态

```bash
cat experiments/v8_sota5_campaign/supervisor/CAMPAIGN_STATUS.md
cat experiments/v8_sota5_campaign/supervisor/CAMPAIGN_MONITOR_STATE.json
```

### 7. 暂停全部实验

```bash
bash experiments/v8_sota5_campaign/pause_all_experiments.sh
```

## 目录结构

```
experiments/v8_sota5_campaign/
  campaign.env
  generate_configs.py       # 生成配置 + phased manifest
  run_from_manifest.py      # 按 manifest 执行（--phases / --categories）
  run_campaign_phased.sh      # Phase 1→4 串行入口
  on_run_complete.sh          # Phase 1 完成后 agent wake
  manifest.csv                # 47 条计划 run（含 phase 列）
  tmux_run_campaign.sh        # 单 tmux 串行启动
  supervisor/                 # 监控 + agent 唤醒

configs/paper/v8_sota5_campaign/
  phase1/                     # Phase 1 优先配置
  ablation/                   # Phase 2 消融
  ours_multiseed/             # Phase 4 多种子
```

## 高级用法

```bash
# 预览 Phase 2
python3 experiments/v8_sota5_campaign/run_from_manifest.py --phases 2 --dry-run

# 前台仅跑 Phase 3 baselines
bash experiments/v8_sota5_campaign/run_campaign_phased.sh 3

# 重新生成 manifest
python3 experiments/v8_sota5_campaign/generate_configs.py
```

## W&B

项目：`https://wandb.ai/<entity>/lora-citb-v8-sota5-paper`

按 Group 筛选：`phase1_priority_instrdialogpp`, `ablation_single_seed`, `baseline_multiseed_*`, `ours_multiseed_*`
