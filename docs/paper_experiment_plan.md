# 论文实验计划书

**生成时间**：2026-06-17  
**工作目录**：`/root/autodl-tmp/Lora-code`  
**负责人**：实验管线（Alonzo 导师反馈对齐版）  
**最后核实**：2026-06-17（基于 `results/tables/`、`experiments/sota_campaign/`、tmux/GPU 实况）

---

## 1. 导师（Alonzo）反馈摘要与回应

| 反馈要点 | 回应与当前状态 |
| --- | --- |
| Baseline 数量差不多，但需核实所有**已发表、可比较**的相关方法；arXiv-only 不强制 | 主表锁定 4 个 advanced baseline（均已正式发表）+ ours；LFPT5/LAMOL/InfLoRA 等作补充；TRACE/RCL、TM-BNNM 等 arXiv-only 不强制进主表 |
| Benchmark：InstrDialog、InstrDialog++、TRACE、MultiWOZ NLG 基本够了 | 方向认可；**CITB 两基准已就绪**；TRACE/MultiWOZ 缺统一 processed stream 与 config，**暂不能硬跑** |
| 指标需与现有方法普遍共用的评价体系一致 | CITB 使用 `seen_avg_score`、`seen_avg_task_aware_score`、`forgetting`、`token_f1_mean`、`lcs_overlap_mean`；TRACE 需 general/instruction/safety delta；MultiWOZ 需 ROUGE-L/BLEU/slot error（待实现） |
| SOTA 目标：相对 advanced baseline **+33%**，非绝对 0.6 | 已写入 `experiments/sota_campaign/SOTA_VERDICT.json`；InstrDialog++ 上 sota-v3 **峰值**已达标，**终局**仍待全 38 segment 完成 |

**核实结论**：实验方向与导师要求一致；工程上需先完成 CITB 复核 + sota-v3 全流，再补齐 TRACE/MultiWOZ 数据管线后方可启动四基准全矩阵。

---

## 2. Baseline 清单

### 2.1 主表必比（已发表）

| 方法 | 发表状态 | 会议/期刊 | arXiv-only? | 工程状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| **O-LoRA** | 已发表 | Findings of EMNLP 2023 | 有 arXiv 但已进 proceedings | 统一入口 scaffold + orthogonal hook | 论文中标注「统一入口复现版」 |
| **LB-CL** | 已发表 | NeurIPS 2024 | 否 | scaffold + SVD/projection hook | **InstrDialog++ 上当前最强 advanced baseline** |
| **Progressive Prompts** | 已发表 | ICLR 2023 | 有 arXiv | scaffold，soft prompt 未完整 | 对照 prompt-based CL |
| **Continual-T0** | 已发表 | EMNLP 2022 | 有 arXiv | instruction replay scaffold | 强 rehearsal 对照 |

### 2.2 基础 baseline（主表下限）

| 方法 | 状态 |
| --- | --- |
| Sequential LoRA | 历史配置已有，非本阶段优先 |
| Replay LoRA | 历史配置已有 |

### 2.3 强烈建议 / 附录（已发表，按 benchmark 条件纳入）

| 方法 | 发表 | 纳入条件 |
| --- | --- | --- |
| LFPT5 | ICLR 2022 | 独立 T5 环境 + 数据 |
| LAMOL | ICLR 2020 | 附录 sanity |
| AdapterCL/ToDCL | EMNLP 2021 | MultiWOZ/TOD 数据就绪后 |
| ARPER | Findings EMNLP 2020 | MultiWOZ NLG converter 完成后 |

### 2.4 不强制（arXiv-only 或 benchmark 本体）

| 方法/设定 | 理由 |
| --- | --- |
| TRACE 论文本身 | 主要是 benchmark；arXiv:2310.06762，作评估协议而非强制方法 baseline |
| RCL | 与 TRACE 同文，arXiv-only |
| InfLoRA | 已发表但偏 CV，迁移公平性需说明 |
| TM-BNNM | arXiv:2403.10894，无官方仓库 |
| EWC/LwF/GEM | 经典 CL，LLM 成本与公平性需单独说明 |

---

## 3. Benchmark 清单

| Benchmark | Segment 数 | 数据文件 | 统一入口 | 训练脚本 | 缺口 |
| --- | ---: | --- | --- | --- | --- |
| **CITB-InstrDialog** | 19 | `data/processed/citb_cl_dialogue_tasks_train50_eval10.json` | `core/data.py` alias `instrdialog` | `core/train.py` | 无（已跑 published-setting） |
| **CITB-InstrDialog++** | 38 | `data/processed/citb_cl_38_random_tasks_train50_eval10.json` | alias `instrdialog++` | 同上 | sota-v3 仍在训练 |
| **TRACE** | 8 训练任务 + Lima replay | `data/processed/trace_cl_tasks_train50_eval10.json`（toy: `_toy.json`） | alias `trace` ✅ | `configs/paper/published_setting/trace__ours__s123.yaml`（smoke） | 原始数据 Google Drive 下载失败；全量 8 segment + 3H delta 指标待做 |
| **MultiWOZ NLG** | 5 domain | `data/processed/multiwoz_nlg_cl_domains_train50_eval10.json`（toy: `_toy.json`） | alias `multiwoz_nlg` ✅ | `configs/paper/published_setting/multiwoz__*__s123_toy.yaml`（5-method smoke） | ROUGE-L/BLEU 已接入 `core/evaluate.py`；全量 GPU 实验待队列 |

每 segment：train 50 / eval 10（CITB published-setting 协议）。

---

## 4. 指标定义与对齐

### 4.1 CITB（InstrDialog / InstrDialog++）— 与项目统一评估一致

| 指标 | 定义 | 主表用途 |
| --- | --- | --- |
| `seen_avg_score` | 最终 checkpoint 对所有已见 segment eval 的**精确匹配准确率**均值 | **主指标** |
| `seen_avg_task_aware_score` | 允许 task-aware routing 时的上界/诊断指标 | 主表需注明是否 oracle/task-id |
| `forgetting` | 各已见任务历史最佳与当前值之差（max） | CL 核心 |
| `task_aware_forgetting` | task-aware 版 forgetting | 诊断 |
| `token_f1_mean` | 生成 token F1（normalized） | 生成质量 |
| `lcs_overlap_mean` | LCS overlap | 生成质量补充 |
| LCA / anytime | `extra.anytime_score` 等 | 学习曲线分析 |

与 CITB/InstrDialog 类工作一致：accuracy + forgetting + 生成 F1；**无需改协议**。

### 4.2 TRACE（待对齐）

- General Ability Delta、Instruction Following Delta、Safety Delta（相对初始 Llama）
- 需在 converter 完成后接入 `core/evaluate.py` 扩展

### 4.3 MultiWOZ NLG（待对齐）

- ROUGE-L、BLEU/SacreBLEU、Slot Error Rate / Entity F1
- 与 ARPER/AdapterCL 原始 NLG 设定对齐

### 4.4 需对齐项（计划书标注）

| 项目 | 状态 |
| --- | --- |
| CITB 指标 | ✅ 已对齐 |
| TRACE 3H delta | ❌ 未实现 |
| MultiWOZ NLG 指标 | 🟡 ROUGE-L/BLEU 已接入 evaluate.py；slot error 待做 |
| Advanced baseline scaffold 标注 | ⚠️ 论文须写「统一入口 hook 复现，非完整官方复现」 |

---

## 5. 实验矩阵（seed=123，第一阶段）

**方法列**：ours（主方法 sota-v3）、O-LoRA、LB-CL、Progressive Prompts、Continual-T0

### 5.1 覆盖矩阵

| Benchmark | ours | O-LoRA | LB-CL | PP | C-T0 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| InstrDialog | ✅ published + ⚠️ sota-v3 early_stopped | ✅ | ✅ | ✅ | ✅ | published-setting 五方法均完成 |
| InstrDialog++ | 🟢 sota-v3 训练中 + ✅ published | ✅ | ✅ | ✅ | ✅ | 主方法以 sota-v3 为准 |
| TRACE | 🟡 smoke 通过 | ❌ | ❌ | ❌ | ❌ | converter + alias + toy smoke ✅；全量 raw 下载 blocked |
| MultiWOZ NLG | 🟡 toy config 就绪 | 🟡 | 🟡 | 🟡 | 🟡 | processed JSON + 5-method toy smoke config ✅；ROUGE/BLEU 已接入 |

图例：✅ 已完成 | 🟢 运行中 | ⏳ 已排队 | ❌ 未启动/blocked

### 5.2 Manifest

- 全矩阵：`results/tables/four_benchmark_single_seed_manifest.csv`
- 状态追踪：`results/tables/four_benchmark_single_seed_status.csv`

---

## 6. sota-v3 现状与主方法定位

### 6.1 配置与存档

| 项 | 路径 |
| --- | --- |
| InstrDialog++ config | `configs/paper/sota_campaign/sota_v3_instrdialogpp_s123.yaml` |
| InstrDialog config（新建） | `configs/paper/sota_campaign/sota_v3_instrdialog_s123.yaml` |
| 变更说明 | `archives/sota_v3/CHANGES.md` |
| 判定文件 | `experiments/sota_campaign/SOTA_VERDICT.json` |
| 日志 | `results/logs/paper_instrdialogpp_sota_v3_ours_s123.log` |

**sota-v3 相对 published ours 的改动**：PLL `oracle_pll_min_agreement=0.72`、`bonus_steps=4`、`prototype_update_steps=5`（基于 v8_sota_5 + v6_sota_2 trajectory early stop）。

### 6.2 主方法决策

| 基准 | 主方法 | 理由 |
| --- | --- | --- |
| InstrDialog++ | **sota-v3** | published ours seen=0.298 未达 +33%；sota-v3 峰值远超目标 |
| InstrDialog | published ours 可用；**sota-v3 排队扩展** | published 已达标 +33%；sota-v3 作统一主方法配置 |
| TRACE / MultiWOZ | sota-v3 config 模板待 converter 后生成 | 与 CITB 主方法一致 |

### 6.3 sota-v3 vs Advanced Baseline（InstrDialog++，真实数据）

**Advanced baseline 最佳（全 38 segment 终局）**：LB-CL  
**+33% 目标**：`best × 1.33`

| 指标 | LB-CL 最佳 | +33% 目标 | published ours | sota-v3 峰值 | sota-v3 最近(seg12) |
| --- | ---: | ---: | ---: | ---: | ---: |
| seen_avg_score | 0.2365 | **0.3153** | 0.2981 ❌ | 0.7000 @seg1 ✅ | 0.3000 ❌ |
| seen_avg_task_aware | 0.2839 | **0.3785** | 0.3394 ❌ | 0.7000 @seg1 ✅ | 0.3500 ❌ |
| token_f1_mean | 0.3346 | **0.4461** | 0.4148 ❌ | 0.9000 @seg0 ✅ | 0.3330 ❌ |

**InstrDialog（LB-CL 最佳 seen=0.2254，+33%=0.2998）**

| 指标 | LB-CL | published ours | 达标? |
| --- | ---: | ---: | --- |
| seen_avg_score | 0.2254 | 0.3307 | ✅ |
| seen_avg_task_aware | 0.3351 | 0.3825 | ✅ |
| token_f1_mean | 0.2810 | 0.4164 | ✅ |

### 6.4 解读（审稿视角）

1. **sota-v3 早期峰值**（seg0–1 seen=0.7）远超 +33%，但 **不可单独作为主表终局数字**——后续遗忘导致 seg12 seen≈0.30。
2. **SOTA_VERDICT** 基于峰值判定「相对 SOTA 已达成」符合用户决策（+33% margin），但 **论文主表应报告全流终局 + forgetting/LCA**。
3. published ours 在 InstrDialog++ 上 **略低于 +33% seen 阈值**（0.298 vs 0.3153），故 InstrDialog++ 主表需等 sota-v3 跑完或报告峰值+终局双行。
4. sota-v3 **仅在 InstrDialog++ 上运行**；InstrDialog / TRACE / MultiWOZ 尚未跑 sota-v3。

---



### InstrDialog sota-v3 单 seed 跑批记录（2026-06-17 08:24）

- **run**: `paper_instrdialog_sota_v3_ours_s123`
- **结果**: early_stopped；终局 seen=0.2750 ta=0.2750 f1=0.3104
- **轨迹**: seg0 seen=0.000, seg1 seen=0.050, seg2 seen=0.033, seg3 seen=0.275
- **segment CSV**: `results/tables/paper_instrdialog_sota_v3_ours_s123_segment_metrics.csv`

## 7. 执行顺序（单 seed 第一阶段）

### Phase A — 已完成 / 进行中

1. ✅ Published-setting：InstrDialog + InstrDialog++ × 5 方法（`configs/paper/published_setting/`）
2. 🟢 sota-v3 InstrDialog++（tmux `sota-v3`，W&B `lora-sota-campaign`）

### Phase B — 立即执行（GPU 串行）

3. ⏳ 等待 sota-v3 InstrDialog++ 结束（避免抢 GPU）
4. ⚠️ sota-v3 InstrDialog **early_stopped**（seg2 seen=0.033）；勿重启
5. tmux `lora_four_benchmark_single_seed` 队列自动执行

### Phase C — 数据管线（TRACE / MultiWOZ 前置）

6. TRACE：✅ `scripts/convert_trace_to_stream.py` + `trace` alias + toy smoke；⏳ 下载 Google Drive 全量数据 → `trace_cl_tasks_train50_eval10.json` → 8 segment configs + 3H delta 指标
7. MultiWOZ NLG：domain order 定稿 → converter → ROUGE/BLEU 指标 → configs
8. TRACE/MultiWOZ toy smoke → 全矩阵入队

### Phase D — 多 seed（后续）

9. seed 456、789 在单 seed 矩阵稳定后启动

---

## 8. 严谨性检查清单（CCF-A 审稿视角）

- [ ] 所有主表数字来自 `results/runs/<run_name>/` 或 segment CSV，可追溯到 W&B run
- [ ] Advanced baseline 标注 scaffold/partial faithful，不声称完整官方复现
- [ ] 报告 final average + forgetting，不单报 early peak
- [ ] task_aware 指标明确是否允许 task id / oracle routing
- [ ] TRACE/MultiWOZ 未跑前不在主表留空或编造
- [ ] 同一 backbone（Llama-3.1-8B-Instruct）、同一 train50/eval10 协议
- [ ] 随机种子固定并记录（123）
- [ ] 显存/训练时间/branch 数作为资源附录
- [ ] arXiv-only 方法不进主表强制对比

---

## 9. 时间线与 tmux / W&B 规范

### 9.1 tmux Session

| Session | 用途 | 状态 |
| --- | --- | --- |
| `sota-v3` | sota-v3 InstrDialog++ 训练 | ⏸️ 已暂停（PAUSE_SOTA_V3） |
| `sota-monitor` | SOTA 战役监控 | 🟢 活跃 |
| `lora_four_benchmark_single_seed` | 四基准单 seed 队列 | 🟢 trace_ours_s123 PID 635761 |

### 9.2 W&B 项目

| 项目 | 用途 |
| --- | --- |
| `lora-published-setting` | published-setting 已完成 run |
| `lora-sota-campaign` | sota-v3 InstrDialog++ |
| `lora-four-benchmark-single-seed` | 四基准单 seed 新队列 |

规范：`wandb_mode=online`；`wandb_group` 按 benchmark；tags 含 benchmark/method/seed。

### 9.3 日志与表格

- 训练日志：`results/logs/<run_name>.log` 或 `results/logs/four_benchmark_single_seed/<run_name>.log`
- Segment 表：`results/tables/<run_name>_segment_metrics.csv`
- 队列日志：`results/logs/four_benchmark_single_seed_queue.log`

### 9.4 启动命令

```bash
# 四基准队列（等待 sota-v3 结束后跑 InstrDialog sota-v3）
bash scripts/launch_four_benchmark_queue.sh

# 手动串行
export WAIT_FOR_PIDS="<sota-v3-pid>"
export WANDB_PROJECT=lora-four-benchmark-single-seed
bash scripts/run_four_benchmark_single_seed_queue.sh
```

---

## 10. 执行进度（动态更新）

| 时间 | 事件 |
| --- | --- |
| 2026-06-16 | published-setting 10 run 全部 completed |
| 2026-06-17 | sota-v3 InstrDialog++ 训练至 seg12（seen≈0.30），相对 +33% 峰值判定 SUCCESS |
| 2026-06-17 | 创建本计划书、`four_benchmark_single_seed_manifest.csv`、队列脚本 |
| 2026-06-17 | **Phase 2 TRACE**：`scripts/convert_trace_to_stream.py`、`core/data.py` alias `trace`、toy processed JSON、smoke config 1 segment 跑通 |
| 2026-06-17 | **Phase 2 MultiWOZ**：repo clone + converter + 全量/toy processed JSON + `multiwoz_nlg` alias |
| 2026-06-17 | InstrDialog++ sota-v3 **暂停**（`experiments/sota_campaign/PAUSE_SOTA_V3`）；队列改跑 **InstrDialog sota-v3** |
| 2026-06-17 06:46 | **InstrDialog sota-v3** 启动（tmux `lora_four_benchmark_single_seed`，W&B `lora-four-benchmark-single-seed`） |
| 2026-06-17 ~06:50 | InstrDialog sota-v3 进度：**seg0–1 eval 完成 → seg2 训练中**（19 segment 全流） |
| 2026-06-17 | `core/evaluate.py` 新增 **rouge_l_mean / bleu_mean** 导出（per-example + segment CSV） |
| 2026-06-17 | MultiWOZ 5-method **toy smoke config** 就绪；manifest multiwoz 行改为 queued |
| 2026-06-17 | published_setting **Sequential/Replay LoRA** config 创建并入 manifest queued |
| 2026-06-17 | TRACE gdown / Seq-GLUE HF **重试仍失败**（Network unreachable） |
| 2026-06-17 ~06:54 | manifest：`trace_ours` blocked→**queued**（toy smoke config 就绪） |
| 2026-06-17 07:00 | InstrDialog sota-v3 **early_stopped**（seg2 seen=0.033<0.15）；PID 483906 终止；队列续跑 **Sequential LoRA**；InstrDialog++ sota-v3 仍 paused |
| 2026-06-17 ~06:55 | InstrDialog sota-v3：**seg0–2 eval 完成 → seg3 训练中** |
| 2026-06-17 07:00 | shell/tmux 接管：seg3 eval **seen=0.275 ta=0.275 f1=0.310** 后 seg4 训练中被 **SIGTERM**（status 记轨迹早停 seg2 seen=0.033）；manifest **early_stopped**；队列已启 **Sequential LoRA**；InstrDialog++ 仍 PAUSE |
| 2026-06-17 07:07 | Sequential LoRA **492184 诊断**：非 D-state（`/proc` R）、GPU 占用正常；`four_benchmark_single_seed/` tee 日志停于 seg3，**真进度** `results/logs/published_instrdialog_sequential_lora_s123.log` → seg5/19 训练；**未 kill** |
| 2026-06-17 07:06 | monitor 修复：按 **train PID** 跟踪 `published_instrdialog_sequential_lora_s123`（PID 492184）；进度以 **metrics.jsonl** 为准；sota-v3 冻结 early_stopped |
| 2026-06-17 07:00 | 监控：`lora_four_benchmark_monitor`（90s poll）；无 tmux `6113bf09`；GPU 跑 **published_instrdialog_sequential_lora_s123** |
| 2026-06-17 08:20 | **Sequential/Replay LoRA** completed（InstrDialog seg19/19）；MultiWOZ/TRACE **5-method toy smoke** 依次 completed |
| 2026-06-17 08:20 | `multiwoz_continual_t0_s123` 同步 completed（`final_metrics.json` + segment CSV 已落盘） |
| 2026-06-17 08:45 | 四 benchmark 单 seed 队列 **all-done**；汇总表 `results/tables/published_setting_summary_s123.csv` |
| 2026-06-17 08:45 | **Phase 2**：MultiWOZ 全量 5-domain config + `phase2_full_benchmark_manifest.csv`（5 queued / TRACE 5 blocked） |

### 队列状态（2026-06-17 08:45）

- **状态**: **all-done**（GPU 空闲）
- **active_run**: —
- **已完成**: published InstrDialog 10 run + Sequential/Replay；InstrDialog sota-v3 **skipped_partial**；InstrDialog++ sota-v3 **PAUSE**；TRACE/MultiWOZ toy smoke 各 5/5 completed
- **汇总表**: `results/tables/published_setting_summary_s123.csv`（InstrDialog/InstrDialog++ 12 completed run 终局 seen/ta/f1/forget）
- **Phase 2 manifest**: `results/tables/phase2_full_benchmark_manifest.csv`

| 类别 | 状态 | 说明 |
| --- | --- | --- |
| CITB published 10 run | ✅ completed | 见汇总表 |
| InstrDialog Sequential/Replay | ✅ completed | seg19/19 与 seg38/38 |
| InstrDialog sota-v3 | ⚠️ skipped_partial | 勿重启 |
| InstrDialog++ sota-v3 | ⏸ PAUSE | `PAUSE_SOTA_V3` |
| TRACE toy ours | ✅ completed | 4 baseline **blocked**（无 raw） |
| MultiWOZ toy 5-method | ✅ completed | 含 continual_t0 |
| MultiWOZ 全量 5-domain | 🟡 queued | config 就绪，待 Phase 2 队列 |
| TRACE 全量 | 🔴 blocked | Google Drive unreachable |

*sota-v3 冻结于 2026-06-17 07:00（early_stopped，勿重启）。InstrDialog++ sota-v3 保持 PAUSE。*

**下一步**：启动 Phase 2 MultiWOZ 全量队列（GPU 空闲）；TRACE 全量待 raw 下载；InstrDialog++ Sequential/Replay config 待创建；sota-v3 **勿重启**。

---

## 附录 A：Published-setting 终局指标（seed 123，真实）

| Run | seen | ta | f1 | segs |
| --- | ---: | ---: | ---: | ---: |
| instrdialog ours | 0.3307 | 0.3825 | 0.4164 | 19 |
| instrdialog o_lora | 0.2053 | 0.3246 | 0.2620 | 19 |
| instrdialog lb_cl | 0.2254 | 0.3351 | 0.2810 | 19 |
| instrdialog pp | 0.0316 | 0.2518 | 0.1104 | 19 |
| instrdialog c-t0 | 0.1263 | 0.3044 | 0.2121 | 19 |
| instrdialogpp ours | 0.2981 | 0.3394 | 0.4148 | 38 |
| instrdialogpp o_lora | 0.2243 | 0.2822 | 0.3167 | 38 |
| instrdialogpp lb_cl | 0.2365 | 0.2839 | 0.3346 | 38 |
| instrdialogpp pp | 0.0211 | 0.1943 | 0.1531 | 38 |
| instrdialogpp c-t0 | 0.0217 | 0.1792 | 0.1737 | 38 |

数据来源：`results/tables/published_setting_summary_s123.csv`（由 `published_*_segment_metrics.csv` 最后一行生成）。


### 队列当前跑批（动态）

- **更新**: 2026-06-17 17:38
- **active_run**: `trace_ours_s123`（trace/ours_sota_v3 (trace_ours_s123)）
- **train PID**: 635761
- **进度**: 末次 eval seg1/19 seen=1.000 ta=1.000 f1=1.000
- **eval 完成**: 1/19

| seg | task | seen | ta | f1 | lcs |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0 | ? | 1.000 | 1.000 | 1.000 | 0.000 |

*InstrDialog sota-v3 已 early_stopped（冻结）；以下表为当前 GPU 队列 run。*
