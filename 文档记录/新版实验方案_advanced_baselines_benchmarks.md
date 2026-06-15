# 新版实验方案：Advanced Baselines 与 Continual Instruction/NLG Benchmarks

生成日期：2026-06-14

## 1. 研究动机与 Introduction 修改建议

当前项目聚焦持续指令微调：在 Llama-3.1-8B-Instruct 上按 segment 顺序学习 CITB-InstrDialog / InstrDialog++，并尝试用 drift detection、LoRA Bank、router 与 anti-overlap 正则减少遗忘。现有问题是 baseline 仍偏初级：sequential LoRA、replay、periodic multi-LoRA、router-only 和 bank-no-router 能证明模块有效，但不足以支撑“相对已发表强方法”的投稿主张。

建议 introduction 从“我们提出一个 LoRA Bank 系统”改为如下更强叙事：

- 现实 instruction agents 会持续接收新任务、新 dialogue domain 与新生成风格，不能假设一次性 multi-task training。
- 现有 continual learning for LLMs 多依赖 task boundary、oracle task id、固定 prompt/adapter 增长或 replay memory；这些假设在 online instruction tuning 中较弱。
- LoRA/PEFT 让持续学习可部署，但新旧低秩更新之间仍会发生 interference；仅堆叠 adapter 或仅 replay 不能解决路由、容量和任务漂移识别问题。
- 本项目应强调“online-ish continual instruction tuning with modular PEFT”：在有限 memory/adapter budget 下，自动检测分布变化、分配或复用 LoRA 分支，并用 anti-overlap 减少表示/参数冲突。

## 2. 相关方法局限性分析

### Replay / rehearsal

代表方法包括 Experience Replay、Continual-T0、LFPT5 伪样本 replay、ARPER prioritized exemplar replay。优势是简单且稳定，尤其在 instruction-tuned backbone 上很强。局限是需要存储旧数据或生成旧数据；memory budget、隐私和在线数据不可回看会影响可用性；在 NLG 中 replay memory 过小还容易过拟合和模式坍缩。

### Regularization

EWC、LwF、OGD/GEM 等方法可减少旧任务参数漂移，但对 LLM 全参或大规模 LoRA 参数估计 Fisher/梯度约束成本较高。它们通常没有显式处理 instruction/task routing，面对长序列 heterogeneous tasks 时稳定性不足。

### Prompt-based continual learning

L2P、DualPrompt、LFPT5、Progressive Prompts 通过 prompt pool 或逐任务 prompt 隔离更新。优点是参数少、对 backbone 侵入小；缺点是 prompt 长度或 prompt 数随任务增长，复杂生成任务上表达能力弱于深层 LoRA，并且非 oracle setting 下 prompt 检索会成为瓶颈。

### LoRA/subspace PEFT continual learning

O-LoRA、InfLoRA、LB-CL 等方法直接约束低秩子空间干扰，是最接近本项目的强 baseline。局限是多数工作默认 task boundary 已知，推理可用 task id 或固定任务顺序；adapter 数量/子空间缓存随任务增长；对 dialogue/NLG 的 ROUGE-L 和 instruction-following 退化关注不足。

### Dialogue/NLG continual learning

ARPER、TM-BNNM 等方法针对 task-oriented dialog NLG 或 DailyDialog/TOD37，关注生成质量和模式坍缩。局限是输入多为 semantic act 或 domain-specific dialogue context，和通用 instruction tuning 格式有差异，需要 adapter/converter 才能公平接入本项目。

## 3. Advanced Baselines 选择清单

| 方法 | 年份 | 类型 | 选择理由 | 复现优先级 |
|---|---:|---|---|---|
| O-LoRA | 2023 | LoRA orthogonal subspace | 语言模型 CL 中最贴近本项目的已发表强基线；无 replay，直接约束 LoRA 干扰 | 高 |
| LB-CL | 2024 | low-rank sensitivity + gradient projection | 在 O-LoRA 基础上强调选择性正迁移，是检验本方法增益的强对手 | 高 |
| Progressive Prompts | 2023 | prompt-based modular CL | 强 prompt baseline，可与 LoRA Bank 的深层 adapter 表达能力对照 | 高 |
| LFPT5 | 2022 | prompt tuning + pseudo replay | O-LoRA/TRACE 常用强基线，覆盖 few-shot/NLG lifelong learning | 中高 |
| Continual-T0 | 2022 | instruction rehearsal | 强 instruction prior + 小比例 replay，适合作为“简单但强”的 rehearsal baseline | 中高 |
| LAMOL | 2020 | generative pseudo replay | NLP lifelong learning 经典强基线，可检验无真实旧数据 replay 是否足够 | 中 |
| TRACE/RCL | 2023 | benchmark + rationale augmentation | 与 aligned LLM CL 直接相关，可补充 general/instruction/safety forgetting | 中 |
| InfLoRA | 2024 | interference-free PEFT | PEFT CL 代表方法，但官方实现偏视觉；作为迁移型强 baseline | 中 |
| AdapterCL / Residual Adapter | 2021 | adapter-based dialogue CL | task-oriented dialogue CL 的模块化强对照，可与 LoRA Bank 的分支隔离比较 | 中 |
| ARPER | 2020 | prioritized replay + adaptive EWC for dialog NLG | 直接覆盖 task-oriented dialog NLG continual setting | 中 |
| TM-BNNM | 2024 | text mixup + nuclear-norm for dialog generation | 针对 replay 过拟合与 mode collapse，补充 NLG 强 baseline | 中低 |

每个方法的 scaffold 已放在 `baselines/advanced_baselines/<method_name>/README.md`，均标注为“复现准备/待实现”。

## 4. Benchmark 调研清单与可用性判断

| Benchmark / 数据集 | 类型 | 与当前实验关系 | 可用性判断 |
|---|---|---|---|
| CITB-InstrDialog | continual instruction tuning, dialogue tasks | 当前已有 processed 文件，19 个 dialogue 相关任务 | 立即可用，作为主 benchmark |
| CITB-InstrDialog++ | continual instruction tuning, mixed NLP + dialogue | 当前已有 processed 文件，38 个任务更长更难 | 立即可用，作为主 benchmark |
| TRACE | aligned LLM continual learning，8 个任务 | 覆盖 domain、code、math、multilingual，并有 general/instruction/safety delta | 高价值，需要写 converter 与下载数据 |
| Super-NaturalInstructions custom streams | 大规模 instruction tasks | CITB 来源数据，可构建更多 task order / domain streams | 可用，但需明确采样协议避免 cherry-pick |
| Continual-T0 8 generation tasks | instruction/generation CL | 可检验强 instruction model + rehearsal | 可用性中等，需 T5/T0 或改造成 Llama 版本 |
| LAMOL 5-task NLP stream | lifelong language learning，QA/classification/semantic parsing 等 | 适合复现实验历史对照，但与当前 dialogue/NLG 主线距离较远 | 可作为附录 sanity，不建议作为主 benchmark |
| Seq-GLUE / Long-CL / SuperGLUE streams | task-incremental NLP classification | 适合 classification accuracy/F1 与 forgetting | 可作为补充，不宜替代 CITB/NLG 主线 |
| MultiWOZ 2.0/2.1 NLG | task-oriented dialogue NLG | ARPER 原始设置，适合 ROUGE-L/BLEU/slot error | 需 semantic act -> instruction/input/output 转换 |
| TOD37 | 37-domain task-oriented dialog generation | TM-BNNM 使用，长 domain stream | 需数据整理，适合作为 NLG 扩展主表或附录 |
| DailyDialog 10-domain | chitchat dialogue generation | 可评估开放域回复生成持续学习 | 需 domain/topic 划分与生成指标 |
| CLINC150 / BANKING77 / HWU64 | intent classification CL | 轻量分类 sanity benchmark | 可作为分类补充，不足以支撑 NLG 主贡献 |
| CoIN | multimodal continual instruction tuning | 2024 MLLM benchmark | 当前 Llama 文本管线不适合，除非扩展多模态 |
| LongMemEval / ContinuityBench | 长期记忆/行为一致性评测 | 更偏交互评估，不是标准训练流 | 暂列后续 robustness，不进主实验 |

主实验建议使用 CITB-InstrDialog、CITB-InstrDialog++、TRACE；NLG 扩展使用 MultiWOZ/TOD37/DailyDialog 二选一或二选二；分类补充可用 Seq-GLUE/CLINC150。

## 5. 实验设置

### 5.1 模型与训练

- Backbone：`meta-llama/Llama-3.1-8B-Instruct`，LoRA target modules 初始保持 `q_proj/v_proj`，后续可扩展到 `k_proj/o_proj/up_proj/down_proj` 做消融。
- 训练入口：统一使用 `python core/train.py --config <yaml>`。
- 数据格式：所有 benchmark 转为 `data/processed` 统一 stream JSON，每个 segment 包含 `train/eval` 的 instruction triples。
- Seeds：至少 3 个 seed：123、456、789；主表报告 mean ± std。
- Memory budget：0%、0.25%、1%、固定 256/512 exemplar 两种设置；所有 replay baseline 与 ours replay ablation 使用同等 budget。
- Adapter budget：控制最大 LoRA branch 数，例如 4/8/16；报告 trainable params 和峰值显存。

### 5.2 对比组

基础 baseline：

- Sequential LoRA
- Replay LoRA
- Periodic Multi-LoRA
- Router-only
- Bank-no-router

Advanced baseline：

- O-LoRA
- LB-CL
- Progressive Prompts
- LFPT5 / Continual-T0 / LAMOL style replay
- TRACE/RCL rationale augmentation
- InfLoRA（迁移版，若 smoke 成功进主表，否则进附录）
- AdapterCL / ARPER / TM-BNNM（dialogue 或 NLG benchmark 上使用）

本项目方法：

- Ours full：drift detector + LoRA Bank + learned router + anti-overlap
- Ours no drift：固定边界或每段分支
- Ours no bank：单 LoRA
- Ours no router：oracle/均匀或最近分支
- Ours no anti-overlap
- Ours memory-free 与 Ours with replay

## 6. Metrics

### Continual learning metrics

- Average Performance / Average Accuracy：学习到第 t 段后，对所有已见任务平均。
- Final Average Performance：最终 checkpoint 在所有任务上的平均。
- Forgetting / Backward Transfer：历史任务最佳性能与最终性能差。
- Forward Transfer：学习新任务前对新任务的零样本/迁移表现。
- Learning Curve Area / LCA：跨时间平均性能，适合对比稳定学习过程。
- Resource metrics：训练时间、峰值显存、adapter 数、trainable params、replay memory size。

### Classification metrics

- Accuracy：适用于 intent、classification、multiple-choice。
- Macro-F1 / Weighted-F1：类别不均衡时必须报告。
- Per-task confusion 或 class-wise F1：作为附录诊断。

### NLG / instruction generation metrics

- ROUGE-L：用户明确要求，作为摘要/生成任务主指标之一。
- BLEU / SacreBLEU：用于 task-oriented NLG 或格式稳定任务。
- BERTScore / BLEURT：可作为语义相似补充，计算成本较高。
- Exact Match / normalized EM：适合答案较短或结构化输出。
- Slot Error Rate / Entity F1：MultiWOZ/TOD NLG 推荐。
- LLM-as-judge：仅作为补充，需要固定 judge prompt、抽样和人工校准。

### TRACE 特有指标

- General Ability Delta
- Instruction Following Delta
- Safety Delta

## 7. 消融设计

### 模块消融

- 去掉 drift detector：验证自动边界识别是否带来收益。
- 去掉 LoRA Bank：检验模块化容量的必要性。
- 去掉 router：检验非 oracle 分支选择是否有效。
- 去掉 anti-overlap：检验冲突约束是否减少遗忘。
- 去掉 replay：比较纯参数隔离与 memory-based 方法。

### 容量与预算消融

- LoRA rank：4 / 8 / 16 / 32。
- Branch budget：1 / 4 / 8 / unlimited。
- Replay budget：0 / 0.25% / 1% / fixed 256 / fixed 512。
- Drift threshold：低/中/高，以及 oracle task boundary upper bound。
- Router training：self-consistency pseudo label、oracle segment label、entropy/margin 变体。

### Benchmark 与顺序消融

- InstrDialog 原顺序 vs 随机顺序。
- InstrDialog++ 原顺序 vs curriculum/grouped order vs adversarial order。
- TRACE 8-task order 与反向 order。
- NLG benchmark domain order，报告 order sensitivity。

## 8. 预期投稿前差距评估

当前项目距离强投稿还存在以下差距：

1. Baseline 强度不足：必须至少完成 O-LoRA、Progressive Prompts、Continual-T0/LFPT5/LAMOL style replay 中的 2-3 个；LB-CL 若能复现会显著增强说服力。
2. Benchmark 覆盖不足：仅 CITB 两个 stream 偏窄；建议加入 TRACE，并至少加入一个 NLG/dialogue generation benchmark（MultiWOZ/TOD37/DailyDialog）。
3. Metrics 不完整：当前结果需补齐 ROUGE-L、Macro-F1、LCA、resource metrics；TRACE 还需 general/instruction/safety delta。
4. Online setting 需要更清楚：明确是否允许 task boundary、是否允许 task id、是否允许 replay old data；主表应避免使用 oracle task id，oracle 只作为 upper bound。
5. 统计稳定性：主结果至少 3 seeds，显著性或 bootstrap CI；不能只报单次最优 run。
6. 工程可复现：advanced baseline 需要统一 config、统一数据转换、统一日志表格；避免每个 baseline 独立脚本导致不公平。

## 9. 推荐执行路线

第一阶段：整理结构与 smoke test。

- 已完成：移动基础 baseline 到 `baselines/basic_baselines/`；创建 advanced baseline scaffold。
- 下一步：更新 baseline loader，使其能从 `basic_baselines` 读取旧方法，或保留兼容 import 路径。
- 在 mock stream 上确认 `sequential_lora` 仍可跑。

第二阶段：主 baseline 复现。

- 先做 O-LoRA、Progressive Prompts、Continual-T0/LAMOL style replay。
- 每个方法先跑 CITB-InstrDialog 3 segments smoke，再跑完整 InstrDialog。
- 成功后扩展 InstrDialog++。

第三阶段：benchmark 扩展。

- 写 TRACE converter，统一字段到 processed JSON。
- 选择 MultiWOZ 或 TOD37 做 NLG stream converter。
- 实现 ROUGE-L、BLEU、Macro-F1、LCA。

第四阶段：主实验矩阵。

- 3 seeds × 3 benchmarks × basic/advanced/ours。
- 按 memory budget 与 adapter budget 做公平对照。
- 输出论文主表、遗忘曲线、资源开销图。

第五阶段：投稿收口。

- 引言聚焦 online modular PEFT continual instruction tuning。
- 相关工作按 replay、regularization、prompt、LoRA subspace、dialogue/NLG CL 分类。
- 把 oracle task id 结果放附录，主表强调无 task id/有限 memory。
