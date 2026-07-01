# 四基准单 seed 实验计划

生成时间：2026-06-17

## 结论

当前论文实验计划的方向是合理的：用 CITB-InstrDialog、CITB-InstrDialog++、TRACE、MultiWOZ NLG 覆盖 instruction/dialogue、长任务流、aligned LLM continual learning 与 task-oriented NLG；用 O-LoRA、LB-CL、Progressive Prompts、Continual-T0 等 advanced baselines 补强主表说服力。

但当前工程状态还不能严谨地直接启动“四个 benchmark 全矩阵”。本项目统一入口 `core/data.py` 只注册了 `instrdialog` 和 `instrdialog++` 两个 processed stream，`data/processed/` 也只有这两个 JSON。TRACE 与 MultiWOZ NLG 仅有外部源码或下游样例，尚无统一 converter、processed stream、正式 config 与指标适配。因此，本轮不能伪造 TRACE/MultiWOZ 配置硬跑；应先跑/复核已就绪的 CITB 两基准，并把 TRACE/MultiWOZ 作为数据转换与配置补齐的前置任务。

## Benchmark 状态

| Benchmark | 当前状态 | 是否可立即进入统一队列 | 缺口 |
| --- | --- | --- | --- |
| CITB-InstrDialog | `data/processed/citb_cl_dialogue_tasks_train50_eval10.json` 已存在；published-setting 单 seed 已有 advanced baselines 与 ours 结果 | 是 | 需修正旧 snapshot 中的过期 failed/queued 状态，统一以 per-segment 表和最新 status 为准 |
| CITB-InstrDialog++ | `data/processed/citb_cl_38_random_tasks_train50_eval10.json` 已存在；published-setting 单 seed 已有 advanced baselines 与 ours 结果 | 是 | `sota-v3` 正在同一基准上继续训练，避免新队列抢资源 |
| TRACE | 外部仓库 `external_baselines/trace_rcl` 已下载并 smoke 编译过 | 否 | 缺本项目统一 converter、processed stream、`core/data.py` alias、TRACE 专属 general/instruction/safety delta 评估适配 |
| MultiWOZ NLG | 外部 ToDCL/ARPER 代码中有 MultiWOZ/NLG 相关数据处理或结果样例 | 否 | 缺 semantic act/dialogue context -> `instruction/input/output` converter、domain stream 定义、BLEU/ROUGE-L/slot error 指标配置 |

## Baseline 分层

### 主表必须

| 方法 | published 状态 | 理由 | 当前工程状态 |
| --- | --- | --- | --- |
| O-LoRA | 已发表，ACL Anthology / CL for language models 方向可引用 | LoRA/subspace continual learning，与本方法最接近 | 统一入口可跑，当前实现是 orthogonal hook scaffold，仍需论文级 faithful 对齐 |
| LB-CL | 已发表或正式论文版本需在参考文献中核实；不可只按 arXiv 口径宣传 | 比 O-LoRA 更强的 low-rank/gradient projection 对照 | 统一入口可跑，但仍是 compact SVD/projection scaffold，README 已说明非完整复现 |
| Progressive Prompts | 已发表，prompt-based continual learning 强 baseline | 对照 prompt 模块化 vs LoRA Bank 深层 adapter | 统一入口可跑，但 soft prompt 训练仍标注为未完整实现 |
| Continual-T0 | 已发表，instruction rehearsal 强 baseline | 代表 instruction rehearsal/replay setting | 统一入口可跑，但当前是 instruction replay scaffold，非完整 T0/T5 mixture 复现 |
| Sequential LoRA | 基础 baseline | 必须给出无 CL 机制的下限 | basic baseline 已有历史配置 |
| Replay LoRA | 基础 baseline | 控制 memory/rehearsal 增益 | basic baseline 已有历史配置 |

### 强烈建议

| 方法 | published 状态 | 理由 | 进入条件 |
| --- | --- | --- | --- |
| LFPT5 | 已发表 | few-shot/lifelong prompt tuning 常见强对照 | 需独立 T5 checkpoint、转换脚本和环境，建议主文或补充表 |
| LAMOL | 已发表，经典 NLP lifelong generative replay | 代表 pseudo replay | 需独立旧依赖环境，优先附录 sanity 或主文补充 |
| AdapterCL / ToDCL | 已发表或正式会议/期刊版本需核实 | dialogue continual learning 模块化 adapter 对照 | MultiWOZ/TOD 数据准备后再跑 |
| ARPER | 已发表 dialogue NLG continual learning 方向 | MultiWOZ NLG 上强相关 | MultiWOZ NLG converter 与 slot/ROUGE/BLEU 指标完成后再跑 |

### 附录/迁移补充

| 方法 | published 状态 | 理由 |
| --- | --- | --- |
| InfLoRA | 已发表，但官方实现偏 CV continual learning | 可作为 PEFT/low-rank 迁移补充，不应强制进主表 |
| EWC / LwF / A-GEM | 经典已发表 CL baselines | 适合作为 regularization/gradient episodic memory 附录，LLM/LoRA 成本与公平性需说明 |
| Router-only / Bank-no-router / no-drift / no-overlap | 本方法消融，不是外部 baseline | 必须用于证明模块贡献，但不替代 published baseline |

### 不强制

| 方法 | 状态 | 理由 |
| --- | --- | --- |
| 纯 arXiv 且未正式发表的方法 | 未发表 | 老师强调 published，不能强制列为主 baseline；可在 related work 或附录作为迁移参考 |
| TRACE/RCL 作为“方法 baseline” | TRACE 本身主要是 benchmark/setting，RCL 需核实发表状态 | 更适合作为 benchmark 与评估协议；若 RCL 未正式发表，不强制进主表 |
| TM-BNNM | 当前未找到专属官方仓库，发表状态与实现需继续核实 | 可作为 NLG 扩展讨论，未完成 faithful 实现前不进主表 |

## 指标体系

主指标：

- `seen_avg_score` / final average performance：最终 checkpoint 在所有已见任务上的平均表现。
- `seen_avg_task_aware_score`：task-aware 上界或诊断指标，主表需明确是否允许 task id。
- `forgetting`：历史任务最佳值与最终值差。
- `token_f1_mean`、`lcs_overlap_mean`：当前统一生成评估可用指标。

TRACE 额外指标：

- General ability delta。
- Instruction following delta。
- Safety delta。

MultiWOZ NLG 额外指标：

- ROUGE-L。
- BLEU / SacreBLEU。
- Slot Error Rate 或 Entity F1。

资源指标：

- 训练时间、峰值显存、adapter/branch 数、trainable params、replay memory size。

## 单 seed 实验矩阵

本轮 seed 固定为 `123`。四基准完整矩阵在 converter/config 补齐后再启动：

| Benchmark | Methods |
| --- | --- |
| InstrDialog | ours、O-LoRA、LB-CL、Progressive Prompts、Continual-T0、Sequential LoRA、Replay LoRA |
| InstrDialog++ | ours、O-LoRA、LB-CL、Progressive Prompts、Continual-T0、Sequential LoRA、Replay LoRA |
| TRACE | ours、O-LoRA、LB-CL、Progressive Prompts、Continual-T0、Sequential LoRA、Replay LoRA；RCL 仅在 published/faithful 状态明确后加入 |
| MultiWOZ NLG | ours、O-LoRA、LB-CL、Continual-T0/Replay、Sequential LoRA、AdapterCL/ToDCL、ARPER |

当前可立即复核的已完成矩阵是 `configs/paper/published_setting/` 下的 InstrDialog 与 InstrDialog++ advanced baselines + ours。TRACE/MultiWOZ 不应加入 manifest，直到 processed JSON 与 config 存在。

## 执行优先级

1. 冻结当前 `sota-v3` 运行，不启动新长训练抢占资源；它当前在 tmux `sota-v3` 中运行。
2. 以 `results/tables/published_*_segment_metrics.csv` 重新生成 published-setting 汇总表，修正旧 snapshot 状态不一致。
3. 实现 TRACE converter：下载/定位 TRACE 数据，映射为统一 `stream[].train/eval[].instruction/input/output`，注册 `trace` alias，并增加 TRACE 指标导出。
4. 实现 MultiWOZ NLG converter：确定 MultiWOZ 版本和 domain order，将 semantic act/context 转成 instruction triples，增加 ROUGE-L/BLEU/slot error。
5. 生成四基准 manifest 与队列脚本，W&B 项目建议 `lora-four-benchmark-single-seed`，tmux session 建议 `lora_four_benchmark_single_seed`。
6. 在 TRACE 与 MultiWOZ toy split smoke 通过后，启动完整队列。

## 队列方案草案

当四基准都具备 config 后，使用如下结构：

```bash
export WANDB_PROJECT=lora-four-benchmark-single-seed
export WANDB_MODE=online
tmux new-session -d -s lora_four_benchmark_single_seed \
  "bash scripts/run_four_benchmark_single_seed_queue.sh"
tmux new-session -d -s lora_four_benchmark_monitor \
  "python scripts/monitor_four_benchmark_single_seed.py --loop"
```

manifest 字段沿用 published-setting：

```text
run_name,benchmark,method,seed,config_path,wandb_project,wandb_group,status
```

队列脚本必须跳过已有 `final_metrics.json` 的 run，并写入 `results/tables/four_benchmark_single_seed_status.csv`。监控脚本只报告失败/卡住，不 kill、不重启。

## sota-v3 对比

`sota-v3` 位于：

- 配置：`configs/paper/sota_campaign/sota_v3_instrdialogpp_s123.yaml`
- 启动脚本：`scripts/launch_sota_v3.sh`
- watchdog：`scripts/sota_v3_watchdog.sh`
- 进度：`sota_progress.md`
- 判定：`experiments/sota_campaign/SOTA_VERDICT.json`
- 日志：`results/logs/paper_instrdialogpp_sota_v3_ours_s123.log`

相对当前 published-setting InstrDialog++ advanced baselines，`sota-v3` 的早期峰值明显更高：判定文件记录 peak `seen_avg_score=0.7000`、`seen_avg_task_aware_score=0.7000`、`token_f1_mean=0.9000`，超过 +33% 相对目标。但它不是完整 38 segment 最终结果，后续轨迹出现下滑，`sota_progress.md` 记录最近 seg11 约 `seen=0.3000`、`ta=0.3500`、`f1=0.3330`，并提示 collapse。因此论文主表不能只引用 early peak；需要等最终 segment 完成后用 final average、forgetting 与 LCA 同时比较。

## 风险与处理

- 当前 advanced baseline 多数仍是 scaffold/partial faithful hook，论文中必须如实标注“统一入口复现版”，避免把 smoke-ready 写成完整官方复现。
- TRACE/MultiWOZ 不存在 processed/config 时不能启动四基准队列。
- 如果 `sota-v3` 占用 GPU，新增长实验必须等待或显式排队，不能并行抢占。
- 纯 arXiv 未发表方法不作为主表强制 baseline；只在附录或 related work 说明。
