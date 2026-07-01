# 复现状态矩阵（Reproduction Status）

**生成日期**：2026-06-17  
**Seed**：123（published_setting 主表）  
**GPU 约束**：🟢 训练进行中（解析 manifest 中）；tmux `lora_four_benchmark_single_seed`

图例：**✅ 已匹配/已完成** | **🟢 运行中** | **⏳ 待跑/queued** | **⏸️ 暂停** | **🟡 Smoke 通过** | **❌ 阻塞/未启动**

---

## 1. Benchmark × Method 总览

### InstrDialog（19 segments）

| Method | 数据 | Config | 终局 CSV | 复现状态 |
| --- | --- | --- | --- | --- |
| **Ours (published)** | ✅ | `instrdialog__ours__s123.yaml` | seen=0.3307 ta=0.3825 f1=0.4164 | ✅ 已匹配 |
| **Ours (sota-v3)** | ✅ | `sota_v3_instrdialog_s123.yaml` | seen=0.2750 ta=0.2750 f1=0.3104 | ⚠️ skipped_partial |
| O-LoRA | ✅ | `instrdialog__o_lora__s123.yaml` | seen=0.2053 ta=0.3246 f1=0.2620 | ✅ 已匹配 |
| LB-CL | ✅ | `instrdialog__lb_cl__s123.yaml` | seen=0.2254 ta=0.3351 f1=0.2810 | ✅ 已匹配 |
| Progressive Prompts | ✅ | `instrdialog__progressive_prompts__s123.yaml` | seen=0.0316 ta=0.2518 f1=0.1104 | ✅ 已匹配 |
| Continual-T0 | ✅ | `instrdialog__continual_t0__s123.yaml` | seen=0.1263 ta=0.3044 f1=0.2121 | ✅ 已匹配 |
| Sequential LoRA | ✅ | `instrdialog__sequential_lora__s123.yaml` | 无 | 🟢 训练中（队列续跑） |
| Replay LoRA | ✅ | `instrdialog__replay_lora__s123.yaml` | 无 | ⏳ published_setting config 已建，manifest queued |
| LFPT5 | 独立 T5 env | 无统一入口 config | — | ❌ 需 LFPT5 独立环境与 checkpoint |

### InstrDialog++（38 segments）

| Method | 数据 | Config | 终局 CSV | 复现状态 |
| --- | --- | --- | --- | --- |
| **Ours (published)** | ✅ | `instrdialogpp__ours__s123.yaml` | seen=0.2981 ta=0.3394 f1=0.4148 | ✅ 已匹配 |
| **Ours (sota-v3)** | ✅ | `sota_v3_instrdialogpp_s123.yaml` | 未完成 | ⏸️ 已暂停（勿重启） |
| O-LoRA | ✅ | `instrdialogpp__o_lora__s123.yaml` | seen=0.2243 ta=0.2822 f1=0.3167 | ✅ 已匹配 |
| LB-CL | ✅ | `instrdialogpp__lb_cl__s123.yaml` | seen=0.2365 ta=0.2839 f1=0.3346 | ✅ 已匹配 |
| Progressive Prompts | ✅ | `instrdialogpp__progressive_prompts__s123.yaml` | seen=0.0211 ta=0.1943 f1=0.1531 | ✅ 已匹配 |
| Continual-T0 | ✅ | `instrdialogpp__continual_t0__s123.yaml` | seen=0.0217 ta=0.1792 f1=0.1737 | ✅ 已匹配 |
| Sequential LoRA | ✅ | `configs/paper/instrdialogpp__seq__s123.yaml` | 无 published CSV | ⏳ 历史 config |
| Replay LoRA | ✅ | `configs/paper/instrdialogpp__replay_b50__s123.yaml` | 无 published CSV | ⏳ 历史 config |
| LFPT5 | 独立 T5 env | 无 | — | ❌ 阻塞 |

### TRACE（8 segments + Lima replay）

| Method | 数据 | Config | 终局 CSV | 复现状态 |
| --- | --- | --- | --- | --- |
| **Ours** | 🟡 toy only | `trace__ours__s123.yaml` (1-seg smoke) | 无 | 🟡 CPU smoke config+data 通过；全量 ❌ raw 未下载 |
| O-LoRA ~ C-T0 | ❌ raw | 无 | — | ❌ 阻塞于 TRACE raw |
| Sequential/Replay LoRA | ❌ raw | 无 | — | ❌ 阻塞于 TRACE raw |

**TRACE 阻塞原因**：Google Drive `gdown` 重试仍失败（`Network is unreachable`，2026-06-17）。

### MultiWOZ NLG（5 domains）

| Method | 数据 | Config | 终局 CSV | 复现状态 |
| --- | --- | --- | --- | --- |
| **Ours** | ✅ full + toy | `multiwoz__ours__s123_toy.yaml` | 无 | 🟡 processed + toy config ✅；ROUGE/BLEU 已接入；GPU smoke ⏳ |
| O-LoRA | ✅ processed | `multiwoz__o_lora__s123_toy.yaml` | — | 🟡 toy config ✅，queued |
| LB-CL | ✅ processed | `multiwoz__lb_cl__s123_toy.yaml` | — | 🟡 toy config ✅，queued |
| Progressive Prompts | ✅ processed | `multiwoz__progressive_prompts__s123_toy.yaml` | — | 🟡 toy config ✅，queued |
| Continual-T0 | ✅ processed | `multiwoz__continual_t0__s123_toy.yaml` | — | 🟡 toy config ✅，queued |
| Sequential/Replay LoRA | ✅ processed | 无 | — | ⏳ 待 config |
| AdapterCL/ARPER | 官方 repo | external_baselines | — | ❌ 需独立 NLG env |

### Seq-GLUE

| Benchmark | 数据 | Config | 复现状态 |
| --- | --- | --- | --- |
| Seq-GLUE | ❌ HF 不可达 | 无 converter | ❌ `datasets` 已装但 HuggingFace `Network unreachable`（2026-06-17 重试） |

---

## 2. Smoke 验证（2026-06-17，CPU only）

脚本：`python scripts/smoke_published_setting_pipeline.py --skip-external`

| 检查项 | 结果 |
| --- | --- |
| CITB processed JSON 解析 | ✅ 19 + 38 segments |
| TRACE toy processed JSON | ✅ 1 segment（smoke truncate） |
| MultiWOZ toy processed JSON | ✅ 1 segment |
| published_setting configs + data load | ✅ 含新增 multiwoz/trace/seq-replay configs |
| published CSV 终局指标 vs 计划书附录 | ✅ 10/10 匹配（容差 1e-3） |
| external_baselines py_compile | ✅ 17 PASS（`--help` NEEDS_ENV 预期） |

**未执行（等 GPU 空闲）**：MultiWOZ/TRACE 1-seg GPU smoke；InstrDialog sota-v3 已轨迹早停；Sequential/Replay 队列续跑中。

---

## 3. 代码路径速查

| 类型 | 路径 |
| --- | --- |
| 统一训练入口 | `core/train.py` |
| 数据加载 | `core/data.py` |
| NLG 指标 | `core/evaluate.py`（`rouge_l_mean`, `bleu_mean`） |
| Published configs | `configs/paper/published_setting/` |
| 终局 CSV | `results/tables/published_*_s123_segment_metrics.csv` |
| Manifest | `results/tables/four_benchmark_single_seed_manifest.csv` |
| TRACE converter | `scripts/convert_trace_to_stream.py` |
| MultiWOZ converter | `scripts/convert_multiwoz_to_stream.py` |
| Smoke 脚本 | `scripts/smoke_published_setting_pipeline.py` |
| 下载清单 | `docs/download_manifest.md` |

---

## 4. 下一步（按优先级）

1. **InstrDialog sota-v3 跑完**（19 seg）→ manifest `completed` → 终局 CSV 入主表
2. **TRACE raw 下载**：网络恢复后 gdown → unzip → `convert_trace_to_stream.py --mode full`
3. **MultiWOZ/TRACE GPU smoke**：1-seg toy（GPU 空闲，不与 sota-v3 冲突）
4. **Sequential/Replay LoRA**：InstrDialog published_setting 入队训练
5. **Seq-GLUE**：HF 网络恢复后下载 GLUE/SuperGLUE 样本 + converter（附录级）
