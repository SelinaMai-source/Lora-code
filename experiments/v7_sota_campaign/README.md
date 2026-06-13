# v7 SOTA 搜索战役

在 `run_v7` 分支上，以 **v8_sota_5 冠军配置**（`configs/paper/v8_sota_5.yaml`）为基座，系统搜索 drift / router / branch 超参，目标是在 **instrdialog** 上超越 v8 线最佳结果，并为后续 **instrdialog++** 与多种子验证做准备。

## W&B

| 项 | 值 |
|----|-----|
| 项目 | `lora-citb-v7-sota` |
| Phase 1 group | `v7_search_phase1` |
| run_name 模式 | `v7_sota_{01..12}_instrdialog_s123` |

## 搜索空间（12 组）

由 `generate_search_space.py` 生成，网格 **2×2×3 = 12**：

### Drift（4 档，2×2）

| 维度 | 取值 |
|------|------|
| `drift.threshold` | 0.025 / 0.020 |
| `drift.anchor_size` | 64 / 32 |
| `drift.anchor_refresh_segments` | 64→1，32→2（与 anchor 配对） |

### Router / Branch（3 档 bundle）

| bundle | max_branches | prototype_update_steps | spawn_sync | prototype_ema |
|--------|--------------|------------------------|------------|---------------|
| `lean` | 12 | 2 | true | 0.8 |
| `champion` | 15 | 3 | true | 0.8（v8_sota_5） |
| `slow_ema` | 15 | 2 | true | 0.9 |

输出配置：`configs/paper/v7_sota/v7_sota_01.yaml` … `v7_sota_12.yaml`  
清单：`experiments/v7_sota_campaign/manifest_phase1.csv`

## 执行顺序（单 GPU 串行）

### Phase 1 — 网格搜索（**当前规划，尚未自动启动**）

- **12 runs**：`v7_sota_01` … `v7_sota_12`
- **固定**：benchmark=`instrdialog`，seed=`123`
- **策略**：按 manifest 顺序串行；仅当存在 `final_metrics.json` 时 `--skip-existing` 跳过
- **预估**：约 12 × 单 run 时长（与 v8_sota_5 instrdialog 同量级）

```bash
cd /root/autodl-tmp/Lora-code
source experiments/v7_sota_campaign/campaign.env   # 待实现 runner 时使用
python3 experiments/v7_sota_campaign/generate_search_space.py

# 训练启动（实现 run_phase1_serial.sh 后）：
# bash experiments/v7_sota_campaign/tmux_run_phase1.sh
```

### Phase 2 — 优胜配置多种子 + 双 benchmark（**后续**）

- 从 Phase 1 选出约 **4** 个 promising 配置
- **4 × 3 seeds × 2 benchmarks = 24 runs**
- seeds：`123, 456, 789`；benchmarks：`instrdialog`, `instrdialog++`
- W&B group 建议：`v7_confirm_multiseed`

### Phase 3 — 论文对照（**后续**）

- 与 v8 冠军、关键 baseline 做并排表；不在本 README 首轮启动范围内

## 目录

```
experiments/v7_sota_campaign/
  README.md                 # 本文件
  generate_search_space.py  # 生成 12 配置 + manifest_phase1.csv
  manifest_phase1.csv         # 生成后产出
  campaign.env                # （runner 实现时）W&B 与路径

configs/paper/
  v7_sota_template.yaml       # 文档化模板
  v7_sota/                    # v7_sota_01..12.yaml
```

## 实验记录文档

`文档记录/` 下已包含 v3–v6 实验 docx（`实验v3.docx` … `实验v6.docx`），供 v7 规划对照；无需从旧路径重复拷贝。

## 分支

```bash
git checkout run_v7
git log -1 --oneline   # bootstrap
```

远程：`origin/run_v7`（orphan bootstrap，无 v1–v6 历史提交）
