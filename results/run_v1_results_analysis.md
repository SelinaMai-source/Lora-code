# Run V1 结果分析报告

## 1. 口径与数据源

本报告以当前仓库中的以下文件作为权威结果源：

- `results/tables/paper_main_results.csv`
- `results/tables/paper_ablation_results.csv`
- `results/paper_results_summary.md`
- `results/debug_report_sequence_behavior_diagnosis.md`
- `results/rp_alignment_progress_report.md`

本报告**不**以 `results/final_package/final_report.md` 为准，因为它与当前 `results/tables/*.csv` 的数字不一致，属于过期打包产物。

一个必须先讲清的口径问题是：

- 当前主表里的 `Ours` 对应的是 `ours_no_overlap` / `winner_ours_no_overlap`。
- 当前 ablation 表里的 `OursFull` 才是 overlap-enabled full stack。
- 因此，任何关于 “anti-overlap 带来提升” 的结论，都必须以 `OursFull` 和主表 `Ours` 的真实对应关系来解释，不能把两者混写。

## 2. 对照 `RP(Lora)_v2` 原始设想

`RP(Lora)_v2` 的核心目标大致可以归纳为四类：

1. `Ours` 在 task-free continual tuning 里，相对 baseline 提升 `seen_avg / anytime`。
2. 相对强 baseline，尤其是 matched-branch 或 replay baseline，减少 forgetting。
3. 用 drift + bank + router 形成一个有说服力的闭环方法，并在 routing / drift 指标上给出证据。
4. 在 `InstrDialog` 与 `InstrDialog++` 上形成较完整、可写论文的结果矩阵。

下面按这个目标来判断目前哪些达到了预期，哪些没有。

## 3. 达到预期的部分

### 3.1 `InstrDialog` 上的 `seen_avg / anytime` 达到了正结果

当前主表里，`instrdialog` 的 `seen_avg` 为：

| method | seen_avg | forgetting | token_f1 | oracle_agreement |
| --- | ---: | ---: | ---: | ---: |
| Sequential | 0.0000 | 0.0389 | 0.0000 | 0.0000 |
| Replay(10) | 0.0000 | 0.0778 | 0.0654 | 0.0000 |
| Replay(50) | 0.0000 | 0.0222 | 0.0438 | 0.0000 |
| PeriodicLatest | 0.0263 | 0.3380 | 0.1552 | 0.0000 |
| BankNoRouter | 0.0211 | 0.1870 | 0.1247 | 0.0000 |
| RouterOnly | 0.0000 | 0.0556 | 0.0731 | 0.7204 |
| Ours (`ours_no_overlap`) | 0.0421 | 0.0824 | 0.0411 | 0.0806 |

在这个口径下，当前主表 `Ours` 的确是 `InstrDialog` 上最好的 `seen_avg`，强于：

- `PeriodicLatest = 0.0263`
- `BankNoRouter = 0.0211`
- 其他 `seen_avg = 0.0000` 的 baseline

如果论文主论点聚焦在 “task-free continual setting 下的 seen-average / anytime 改善”，那么这部分是成立的。

### 3.2 相对固定 schedule 的多 LoRA，当前方法更稳

`PeriodicLatest` 的 forgetting 是 `0.3380`，而当前主表 `Ours` 是 `0.0824`。  
这说明相对“固定周期新开 LoRA + latest-only inference”这类 capacity baseline，目前的 drift/bank/routing 方案至少在稳定性上明显更合理。

### 3.3 行为诊断链路已经比较完整

当前仓库已经有：

- 开放环行为诊断
- first-token margin 分析
- prefix forcing 分析
- BOS 修复前后对比

这使得“为什么主指标没有全面变好”可以被更清晰地解释，而不是只给一个 end metric。对于后续论文写作，这是重要资产。

### 3.4 一项明确有效的工程优化已经被验证

根据 `results/rp_alignment_progress_report.md`：

- generation-time duplicated `BOS` 修复后，overfit exact match 从 `1/8` 提升到 `3/8`
- first-token failures 从 `6` 降到 `4`

这说明 repo 已经识别并修掉了一个真实 pipeline bug。它还没有彻底解决 sequence behavior 问题，但它确实带来了可验证的收益。

## 4. 没有达到预期、或弱于 baseline 的部分

### 4.1 Forgetting 没有赢过强 baseline

如果按 `RP(Lora)_v2` 的原始设想，希望 `Ours` 在遗忘上也能形成优势，那么目前这条并没有成立。

`instrdialog` 上：

- `Ours = 0.0824`
- `Replay(50) = 0.0222`
- `Sequential = 0.0389`
- `RouterOnly = 0.0556`

也就是说：

- `Ours` 明显输给 `Replay(50)`
- `Ours` 也输给 `Sequential`
- 它只明显好于 `PeriodicLatest`

因此当前更准确的说法是：  
`Ours` 在 `seen_avg` 上有优势，但在 `forgetting` 上不是当前最优方法。

![InstrDialog main metrics](results/analysis_figures/instrdialog_main_tradeoffs.png)

### 4.2 `token_f1` 明显弱于最强 baseline

当前 `instrdialog` 上：

- `PeriodicLatest = 0.1552`
- `BankNoRouter = 0.1247`
- `RouterOnly = 0.0731`
- `Replay(10) = 0.0654`
- `Replay(50) = 0.0438`
- `Ours = 0.0411`

所以当前主表 `Ours` 并没有在 open-loop generation proxy 上领先，反而处于靠后位置。  
这和 sequence diagnosis 给出的结论一致：当前主要瓶颈仍然是 `first-token margin too weak`，说明 continual learning 本身之外，decode-time / early-token behavior 仍在污染最终指标。

### 4.3 Routing 质量没有兑现成最终效果

目前最尴尬的一点是：

- `RouterOnly` 的 `oracle_agreement = 0.7204`
- 当前主表 `Ours` 的 `oracle_agreement = 0.0806`
- 但 `RouterOnly` 的 `seen_avg = 0.0000`

这意味着至少当前这版实现下：

1. 单看 routing quality，并不能保证下游任务表现。
2. 当前 `Ours` 的 router 也没有形成强而稳定的分支选择能力。
3. 训练时仍然是 segment-wise active-branch 更新、而不是 routed training，这很可能就是 router 证据链不够强的直接原因。

![Routing vs performance](results/analysis_figures/routing_vs_performance.png)

### 4.4 Drift detector 过于保守，漏报太高

当前主表 `Ours` 的 drift 指标为：

- `false_alarm_rate = 0.0000`
- `miss_rate = 0.8889`
- `detection_delay_mean = 9.5`

这说明 detector 几乎不误报，但代价是大量漏报，整体偏保守。  
如果 `RP(Lora)_v2` 的目标是把 drift detection 当成一个可靠的核心模块，那目前的证据仍然不够强。

![Drift diagnostics](results/analysis_figures/drift_diagnostics.png)

### 4.5 Anti-overlap 目前不是正结果，反而是风险点

当前 repo 的实际口径是：

- 主表 `Ours` = `ours_no_overlap`
- `OursFull` 作为 ablation 表中的 overlap-enabled row，结果是：
  - `seen_avg = 0.0000`
  - `token_f1 = 0.0000`
  - `forgetting = 0.1370`

这意味着，在当前单 seed 结果里，anti-overlap 还不能被写成“带来提升”的模块。  
更准确的结论是：它现在是一个尚未调通或尚未被验证的风险点。

![Ours ablations](results/analysis_figures/ours_ablation_heatmap.png)

### 4.6 `InstrDialog++` 覆盖仍然不完整

当前 `instrdialog++` 主表里只有这些 completed rows：

- `BankNoRouter`
- `PeriodicLatest`
- `Replay(10)`
- `Replay(50)`

而：

- `RouterOnly` 仍在 missing/running
- `Ours` 还没有进入当前主表

所以目前还不能写跨 benchmark 的 routed-method claim，更不能写 `Ours` 在两个 benchmark 上都成立。

## 5. 对当前结果的总体判断

如果严格对照 `RP(Lora)_v2` 的原始设想，当前结果最准确的概括是：

- **达预期**：`InstrDialog` 上的 `seen_avg / anytime`，以及相对 `PeriodicLatest` 的稳定性改进。
- **部分达预期**：bank/routing/drift 这条工程链已经接通，也有一定模块效应，但证据还不够闭合。
- **未达预期**：forgetting、token_f1、routing 说服力、drift 检测质量、anti-overlap 正贡献、跨 benchmark 覆盖。

因此，现在的 repo 更像是：

- 一个已经跑通、而且有明确亮点的 research prototype；
- 但还不是一个可以直接把 full stack 作为稳定正结果写进论文主结论的版本。

## 6. 优化建议

### 6.1 第一优先级：先把“训练-推理不一致”修掉

当前最大的结构性问题不是单个超参，而是：

- 训练时主要更新 active branch
- 推理时才按样本路由

这会削弱 router 的学习信号，也会让 `oracle_agreement` 与下游效果脱钩。

建议优先做：

1. 实现真正的 routed training variant。
2. 至少做一个小规模对照：segment-wise training vs routed training。
3. 重新比较 `oracle_agreement` 与 `seen_avg / token_f1` 是否一起改善。

### 6.2 第二优先级：先修 sequence behavior，再看 continual 指标

从现有 diagnosis 看，`first-token margin too weak` 仍然是主瓶颈。  
这意味着如果不先改善早期 token 行为，continual learning 的增益会被 generation failure 吃掉。

建议优先尝试：

1. 针对 first token 的格式/监督增强。
2. 小范围检查 prompt formatting、decode config、answer span 对齐。
3. 针对 `prefix_len = 0/1/3/5` 的行为再做一轮可复现实验，确认问题是在 first token 还是 deeper rollout。

### 6.3 第三优先级：把 drift detector 从“几乎不触发”调成“可用”

建议按 `RP(Lora)_v2` 的原计划优先补几类 sweep：

1. threshold / slack sweep
2. anchor size sweep
3. monitor interval sweep
4. proxy shift labeling 重新定义

目标不是继续压低 false alarm，而是先把 `miss_rate` 从当前的 `0.8889` 明显拉下来。

### 6.4 第四优先级：把 anti-overlap 当成待修复模块，而不是既定贡献

当前最合理的做法不是继续把 overlap 写成成功模块，而是先排查：

1. overlap loss 权重是否过大
2. 该项是否和 LoRA update scale 冲突
3. `OursFull = 0.0000` 是否存在训练/评测路径 bug

只有当 `OursFull` 至少回到与 `ours_no_overlap` 可比较的水平，anti-overlap 才值得重新作为主要贡献推进。

### 6.5 第五优先级：补齐 `InstrDialog++`

在当前状态下，补齐 `InstrDialog++` 的 `RouterOnly` 和 `Ours` 主表结果非常重要。  
否则所有 cross-benchmark claim 都只能停留在“未完成”。

## 7. 建议的后续验收标准

如果希望下一轮结果更接近论文可写状态，我建议至少满足以下条件中的大部分：

1. `InstrDialog` 上 `Ours` 继续保持 `seen_avg` 优势。
2. `forgetting` 至少不要输给 `Sequential`。
3. `token_f1` 至少恢复到不弱于 `Replay(50)`，最好接近 `BankNoRouter`。
4. `oracle_agreement` 明显高于当前 `0.0806`。
5. `miss_rate` 明显低于当前 `0.8889`。
6. `OursFull` 不再明显差于 `ours_no_overlap`。
7. `InstrDialog++` 主表补齐 routed rows。

如果这些条件仍然达不到，那么论文叙事最好收缩成：

- “我们实现了一个 task-free online LoRA pipeline”
- “它在 seen-average 上有积极信号”
- “但 drift / router / overlap 仍然存在关键未解问题”

而不是直接把 full stack 写成成熟方法。
