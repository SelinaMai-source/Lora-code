# published_setting_run_v2 执行计划

**项目**: `lora-published-setting-run_v2`  
**工作目录**: `/root/autodl-tmp/Lora-code`  
**更新**: 2026-06-17

---

## 目标

在 **published_setting** 配置（非 sota-v3）下，单 seed（123）串行完成 **8 methods × 5 benchmarks = 40** 个 full run。  
主方法 **Ours** 使用 `configs/paper/published_setting/*__ours__s123.yaml`；**不触碰** `PAUSE_SOTA_V3` 与 sota-v3 队列。

## 完整矩阵（8×5）

### 方法

| 方法 key | 显示名 | 入口 |
| --- | --- | --- |
| sequential_lora | Sequential LoRA | `core/train.py` |
| replay_lora | Replay LoRA | `core/train.py` |
| o_lora | O-LoRA | `core/train.py` |
| lb_cl | LB-CL | `core/train.py` |
| progressive_prompts | Progressive Prompts | `core/train.py` |
| continual_t0 | Continual-T0 | `core/train.py` |
| lfpt5 | LFPT5 | `scripts/run_lfpt5_published_setting.py`（T5 独立环境） |
| ours | Ours | `core/train.py` (`mode: ours`) |

### 基准

| 基准 | Segments | 数据文件 | v2 基线状态 |
| --- | ---: | --- | --- |
| instrdialog | 19 | `citb_cl_dialogue_tasks_train50_eval10.json` | ✅ 7/7 法 completed |
| instrdialogpp | 38 | `citb_cl_38_random_tasks_train50_eval10.json` | ✅ 7/7 法 completed |
| multiwoz_nlg | 5 | `multiwoz_nlg_cl_domains_train50_eval10.json` | ✅ 7/7 法 completed |
| trace | 8 | `trace_cl_tasks_train50_eval10.json` | ✅ 7/7 法 completed |
| seqglue | 8 | `seqglue_cl_tasks_train50_eval10.json` | 🟡 gap 队列（8 法待跑） |

**Gap 列**：每基准缺 LFPT5（1 列）；Seq-GLUE 为全新 8 法 × 1 基准。

## 进度（2026-06-17）

| 指标 | 值 |
| --- | ---: |
| v2 已完成 | 28（7×4，无 LFPT5 / Seq-GLUE） |
| 全矩阵目标 | 40 |
| Gap 待跑 | 见 `published_setting_run_v2_gap_manifest.csv` |
| 缺口审计 | `results/tables/full_matrix_gap_audit_s123.csv` |

## 文件

| 文件 | 用途 |
| --- | --- |
| `results/tables/full_matrix_gap_audit_s123.csv` | 40-cell 审计（completed/missing/blocked/queued） |
| `results/tables/published_setting_run_v2_gap_manifest.csv` | 仅 missing/blocked/queued |
| `results/tables/published_setting_run_v2_manifest.csv` | 原 v2 manifest（28 行） |
| `scripts/run_published_setting_run_v2_gap_queue.sh` | Gap 串行队列 |
| `scripts/convert_seqglue_to_stream.py` | Seq-GLUE HF → processed JSON |
| `scripts/run_lfpt5_published_setting.py` | LFPT5 wrapper |
| `docs/lfpt5_published_setting.md` | LFPT5 阻塞说明与 smoke 步骤 |

## tmux

| Session | 内容 |
| --- | --- |
| `lora_published_setting_run_v2_gap` | Gap 训练队列（Seq-GLUE + LFPT5 blocked 跳过） |
| `lora_published_setting_run_v2_supervisor` | 原 v2 监督（28/28 已完成） |

## W&B

所有 full config 的 `logging.wandb_project` / `output.tracking.wandb_project` = `lora-published-setting-run_v2`。

## 队列规则

1. 已有 `final_metrics.json` → skip
2. LFPT5 无 T5 checkpoint → `blocked`（不伪造结果）
3. Seq-GLUE processed 就绪 → `queued` → `core/train.py`
4. 单 GPU：`pgrep core/train.py` 等待为空
5. **勿重启** sota-v3（`PAUSE_SOTA_V3`）

## 重新生成 gap 表

```bash
python scripts/convert_seqglue_to_stream.py          # 若 raw 更新
python scripts/gen_gap_published_setting_configs.py  # 13 个新 config
python scripts/gen_full_matrix_gap_audit_s123.py
python scripts/gen_published_setting_run_v2_gap_manifest.py
```

## 启动 gap 队列

```bash
tmux new-session -d -s lora_published_setting_run_v2_gap \
  'cd /root/autodl-tmp/Lora-code && bash scripts/run_published_setting_run_v2_gap_queue.sh'
```

## Seq-GLUE 数据

- Raw：`data/raw/seqglue/glue_*` + `super_glue_*`（HF via clash 代理，2026-06-17 成功）
- Processed：`data/processed/seqglue_cl_tasks_train50_eval10.json`（8 tasks, train50/eval10）
- 任务序：sst2 → mrpc → rte → cola → boolq → wic → cb → copa

## LFPT5

- 源码：`external_baselines/lfpt5/`
- **阻塞**：`assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin` 未下载
- InstrDialog/InstrDialog++ 可通过 wrapper 导出 stream；完整训练需 T5 环境

## 与旧队列关系

- **已完成**: `lora_published_setting_run_v2` 28/28
- **冻结**: sota-v3（`PAUSE_SOTA_V3`）
