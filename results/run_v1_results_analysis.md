# Run V1 结果分析报告

## 1. 分析范围与数据来源

本报告围绕 `RP(Lora)_v2.pdf` 中 `ours` 方法的四个核心设计模块展开：

1. `drift detection`
2. `LoRA bank / capacity allocation`
3. `router / task-free inference`
4. `anti-overlap regularization`

分析所依据的结果文件如下：

- `results/tables/paper_main_results.csv`
- `results/tables/paper_ablation_results.csv`
- `results/paper_results_summary.md`
- `results/debug_report_sequence_behavior_diagnosis.md`
- `results/rp_alignment_progress_report.md`

本报告不采用 `results/final_package/final_report.md` 作为结果来源，原因在于该文件与当前 `results/tables/*.csv` 的数字存在不一致，因此不适合作为本轮分析的权威依据。

## 2. 方法定义与结果口径

在解释当前实验结果之前，有必要说明本轮结果表中的方法映射关系：

- 主表中的 `Ours` 对应 `ours_no_overlap` / `winner_ours_no_overlap`。
- ablation 表中的 `OursFull` 才对应带 anti-overlap regularization 的 full stack 配置。

这一映射关系直接影响 `anti-overlap` 板块的结论解释，因此后文凡涉及 overlap 模块，均以主表 `Ours` 与 `OursFull` 的对照为准，而不将两者视为同一方法。

## 3. 整体结论

当前结果对 `RP(Lora)_v2` 四个 method block 的支持强度可概括如下。

| method block | 当前判断 | 主要正证据 | 主要不足 |
| --- | --- | --- | --- |
| Drift detection | 部分成立 | 关闭 drift 后，`seen_avg` 由 `0.0421` 降至 `0.0053` | `miss_rate = 0.8889`，检测器过于保守 |
| LoRA bank / capacity allocation | 部分成立，且是当前最主要的正结果来源 | `Ours.seen_avg = 0.0421`，高于 `PeriodicLatest = 0.0263`、`BankNoRouter = 0.0211`；`OursNoBank.seen_avg = 0.0000` | forgetting 仍明显弱于 `Replay(50)` 与 `Sequential` |
| Router / task-free inference | 模块有增益，但证据链未闭合 | `Ours.seen_avg = 0.0421`，高于 `OursNoRouter = 0.0158` | `RouterOnly` 的 `oracle_agreement = 0.7204` 未转化为性能收益；`Ours` 自身 `oracle_agreement = 0.0806` 偏低 |
| Anti-overlap regularization | 当前未被实验结果支持 | 已实现该模块并记录 overlap proxy | `OursFull` 明显弱于主表 `Ours`，当前不能支持其优于 baseline 的结论 |

总体而言，当前结果对 `drift + bank` 改善 `seen_avg / anytime` 的支持相对充分；证据最薄弱的板块是 `anti-overlap regularization`，其次为 `router` 与 `drift detector` 的独立证成。

## 4. Drift Detection

### 4.1 设计目标

`RP(Lora)_v2` 对 drift detection 的目标并不限于“系统中存在一个 detector”。更严格的目标包括：

- 在 task-free instruction stream 中识别具有实质意义的分布变化；
- 在保证较低 `false_alarm_rate` 的同时，控制 `detection_delay`；
- 相比固定 schedule 的分支扩容策略，更合理地触发新 branch 的创建，从而改善后续表现。

### 4.2 支持该模块有效性的结果

当前最直接的证据来自 `Ours` 与 `OursNoDrift` 的对照：

- `seen_avg`: `Ours = 0.0421`，`OursNoDrift = 0.0053`
- `forgetting`: `Ours = 0.0824`，`OursNoDrift = 0.1546`

这一结果表明，drift 相关设计在当前单 seed 结果下并非冗余模块，而是对 `seen_avg` 和 forgetting 都具有实质性贡献。

此外，与固定 schedule baseline 相比：

- `Ours.forgetting = 0.0824`
- `PeriodicLatest.forgetting = 0.3380`

这一对比虽不能将全部收益完全归因于 detector 本身，但至少说明“基于检测结果决定何时扩容”优于“固定频率扩容”的整体路线。

![图 1. Drift detection 模块的证据图：左图显示 `Ours` 相比 `OursNoDrift` 在 `seen_avg` 和 forgetting 上具有明显优势；右图显示 detector 自身的质量指标仍然较弱。](results/analysis_figures/method_block_drift.png)

### 4.3 相对 baseline 的不足

若按 `RP(Lora)_v2` 对 drift quality 的原始标准衡量，当前 detector 的主要不足十分明确：

- `false_alarm_rate = 0.0000`
- `miss_rate = 0.8889`
- `detection_delay_mean = 9.5`

这表明检测器几乎不误报，但代价是大规模漏报，且触发滞后明显。该结果并不满足 `v2` 中“低误报、低延迟、可识别真实 shift”的目标设定。

此外，当前实现与 `v2` 原始方案之间仍存在两处偏差：

1. `v2` 设想的是按固定 `K` 步频率监控，而当前实现主要按 segment 监控。
2. 当前 drift quality 仍采用 proxy 口径，将 inter-segment boundary 视为 candidate shift，而非更精细的 shift annotation。

因此，更准确的表述应为：drift 模块对系统主指标有帮助，但 detector 本身尚未被证明是一个成熟可靠的 change-point detector。

### 4.4 优化建议

该板块的优先优化方向如下：

1. 对 `threshold / slack / anchor size / monitor interval` 做系统 sweep。
2. 重新定义 proxy shift label，避免将所有 inter-segment boundary 统一视为正例。
3. 尽量回到更接近 `v2` 的高频监控方式，而非纯 segment-level 监控。
4. 在论文叙事中区分“drift 模块对全系统有帮助”与“detector 本身已被独立证成”这两个层次。

## 5. LoRA Bank / Capacity Allocation

### 5.1 设计目标

`RP(Lora)_v2` 对 LoRA bank 的期待主要包括：

- drift 发生后冻结旧 branch，并由新 branch 承接新分布；
- 通过显式 capacity allocation 减少 sequential interference；
- 在 matched branch budget 下，相比 `Sequential` 与 `PeriodicLatest` 取得更高的平均表现，并尽可能降低 forgetting。

### 5.2 支持该模块有效性的结果

LoRA bank 是当前 `ours` 方法中证据最充分的正结果来源之一。

主表 `instrdialog` 上：

- `Ours.seen_avg = 0.0421`
- `PeriodicLatest.seen_avg = 0.0263`
- `BankNoRouter.seen_avg = 0.0211`
- `Sequential.seen_avg = 0.0000`

消融结果则进一步显示：

- `OursNoBank.seen_avg = 0.0000`

这说明 bank 并非附加性的工程组件，而是当前 `seen_avg` 增益的重要来源。

从稳定性角度看：

- `Ours.forgetting = 0.0824`
- `PeriodicLatest.forgetting = 0.3380`

因此，至少相对于固定 schedule 的多 LoRA 基线，当前 bank-based capacity allocation 具有明显优势。

![图 2. LoRA bank / capacity allocation 模块的证据图：左图比较主表各基线的 `seen_avg`；右图显示 `OursNoBank` 会使 `seen_avg` 退化到 `0.0000`，但 forgetting 仍未优于最强 baseline。](results/analysis_figures/method_block_bank.png)

### 5.3 相对 baseline 的不足

若按 `v2` 更强的目标衡量，LoRA bank 仍未在 forgetting 上形成全面优势：

- `Replay(50).forgetting = 0.0222`
- `Sequential.forgetting = 0.0389`
- `Ours.forgetting = 0.0824`

这意味着该模块当前可以支持如下结论：

- 相对 `PeriodicLatest` 等 fixed-schedule baseline，LoRA bank 路线更合理；
- 相对 replay-heavy baseline，当前方案仍未达到更优 forgetting；
- 即使与 `Sequential` 相比，当前 forgetting 也尚未形成优势。

因此，该板块当前较稳妥的 claim 是：LoRA bank 在 `seen_avg / anytime` 上已经形成积极信号，但尚不能据此宣称其在 forgetting 上优于强 baseline。

此外，`instrdialog++` 仍缺少 routed `Ours` 主行，因此该板块也尚不足以支撑跨 benchmark 的强结论。

### 5.4 优化建议

建议优先从以下方向推进：

1. 继续调优 branch budget、spawn frequency 与 merge policy。
2. 研究是否需要极小 replay 或更轻量的 retention regularization，以改善 forgetting。
3. 检查新 branch 初始化和 warm-start 策略，避免旧能力在切换时被过度割裂。
4. 在论文叙事中优先强调 `seen_avg / anytime`，而非过早扩展为“全面优于 replay”。

## 6. Router / Task-Free Inference

### 6.1 设计目标

`RP(Lora)_v2` 对 router 的目标较为严格：

- 在无 task ID 的条件下，为每个样本选择合适 branch；
- `RouterOnly` 至少应相对 `PeriodicLatest` 提供 measurable gain，或清楚暴露其局限；
- `Ours` 中的 task-free inference 应形成一个可解释的闭环收益。

### 6.2 支持该模块有效性的结果

当前关于 router 的正证据主要来自消融对照，而非 standalone baseline：

- `Ours.seen_avg = 0.0421`
- `OursNoRouter.seen_avg = 0.0158`

与此同时：

- `Ours.forgetting = 0.0824`
- `OursNoRouter.forgetting = 0.1408`

这一结果表明，router 对当前 `Ours` 的主结果具有实质性贡献，而非纯粹无效的附加模块。

### 6.3 相对 baseline 的不足

当前 router 的问题不在于“没有任何效果”，而在于证据链并未闭合。

首先，`RouterOnly` 的表现说明高 `oracle_agreement` 并不自动转化为任务性能：

- `RouterOnly.oracle_agreement = 0.7204`
- `RouterOnly.seen_avg = 0.0000`

其次，当前主表 `Ours` 的 router quality 本身并不强：

- `Ours.oracle_agreement = 0.0806`

此外，当前实现仍存在结构性限制：

- 训练过程中主要按 segment 更新 active branch；
- router 的 per-example selection 主要发生在 evaluation；
- 因而训练与推理尚未形成真正闭环。

因此，该板块当前更准确的结论是：router 对 `Ours` 的主结果有帮助，但其作为一个独立成熟的 task-free inference solution 仍缺乏充分证据。

![图 3. Router 模块的证据图：左图显示 `RouterOnly` 的高 `oracle_agreement` 未能转化为 `seen_avg` 增益；右图显示 router 在 `Ours` 内部具有增益，但闭环机制仍不充分。](results/analysis_figures/method_block_router.png)

### 6.4 优化建议

该板块的优先优化方向应首先聚焦于结构性修正，而非局部调参：

1. 实现真正的 routed training，而不仅在 evaluation 时 per-example route。
2. 重构 pseudo-label 生成和 margin filtering，使监督信号更稳定、且更接近推理分布。
3. 检查 branch utilization 是否发生塌缩，必要时引入 balance constraint。
4. 在写作中将 `RouterOnly` 更明确地作为“暴露局限”的 baseline，而非既定正结果。

## 7. Anti-Overlap Regularization

### 7.1 设计目标

`RP(Lora)_v2` 对 anti-overlap 的原始设想是 activation-space diversity regularization，其预期目标为：

- 降低 branch redundancy；
- 提高 routing stability；
- 最终改善 specialization 与主任务性能；
- 在 overlap metric 与主结果两方面同时形成正向证据。

### 7.2 当前已完成的部分

目前可以确认的正向事实主要有两点：

- 代码路径中已经实现了 anti-overlap 相关训练项；
- 系统会记录 overlap proxy，可用于后验监控。

因此，该模块在“工程存在性”层面已经完成，但在“实验有效性”层面尚未被当前结果支持。

### 7.3 相对 baseline 的不足

首先，当前实现与 `v2` 原始设想已有方法学偏移：

- `v2` 预期的是 activation-space diversity loss；
- 当前实现是 orthogonal-weight regularization，activation space 主要用于监控而非直接优化目标。

其次，从结果上看：

- 主表 `Ours = ours_no_overlap`
- `Ours.seen_avg = 0.0421`
- `Ours.token_f1 = 0.0411`
- `OursFull.seen_avg = 0.0000`
- `OursFull.token_f1 = 0.0000`

该结果说明，在当前单 seed 条件下，带 overlap 的 `OursFull` 明显弱于主表赢家，因而不能支持如下结论：

- anti-overlap 优于 baseline；
- anti-overlap 带来了稳定的 specialization gain。

更准确的结论应为：anti-overlap 当前仍是待修复模块，而非已验证贡献。

![图 4. Anti-overlap 模块的证据图：主表赢家 `Ours(main=no_overlap)` 与 `OursFull` 直接对照显示，当前 overlap-enabled 配置尚未形成正收益。](results/analysis_figures/method_block_overlap.png)

### 7.4 优化建议

建议优先从以下方面排查：

1. 重新进行 `beta` sweep，而不默认当前 loss 权重是合理的。
2. 检查 overlap loss 是否与 LoRA scale、branch 数量、训练步数发生冲突。
3. 若后续叙事仍希望与 `v2` 对齐，可考虑回到 activation-space regularization，而非继续仅依赖 weight-space proxy。
4. 在 `OursFull` 至少恢复到接近 `ours_no_overlap` 的水平之前，不宜将 anti-overlap 继续作为主贡献。

## 8. 跨模块影响因素：Sequence Behavior

尽管 sequence behavior 并非 `v2` 中单列的 method block，但它当前对四个板块的结果解释均具有重要影响。

现有诊断中最明确的结论包括：

- `first-token margin too weak`
- `count_first_token_wrong = 5`
- `count_extra_preamble = 2`
- BOS 修复后，overfit exact match 从 `1/8` 提升到 `3/8`

这些结果说明，若仅优化 drift / bank / router / overlap，而不同时处理 sequence-level behavior，仍可能出现如下局面：

- `seen_avg` 获得一定改善；
- 但 `token_f1` 与 open-loop quality 的提升幅度有限。

因此，sequence behavior 不应被视为外围问题，而应被纳入后续优化优先级。

## 9. 结论与优先级建议

若以 `RP(Lora)_v2` 中四个 method block 为评价对象，则当前阶段最合理的结论如下：

1. `drift detection`：模块层面部分成立，但 detector quality 本身未达预期。其优势体现在 `Ours` 相对 `OursNoDrift` 的 `seen_avg` 与 forgetting 改善；其不足在于极高的 `miss_rate`。
2. `LoRA bank / capacity allocation`：这是当前证据相对最充分的正结果板块。其优势主要体现在 `seen_avg / anytime` 相对 `Sequential`、`PeriodicLatest` 和 `BankNoRouter` 的提升；其不足在于 forgetting 仍输给 `Replay(50)` 与 `Sequential`。
3. `router / task-free inference`：当前可证明其对 `Ours` 内部有效，但尚不能证明其已形成成熟、独立的 task-free inference solution。最大问题是高 agreement 与实际任务收益之间仍存在明显脱钩。
4. `anti-overlap regularization`：当前结果不足以支持其正贡献。与其将其写成已经成立的核心贡献，更合适的处理方式是将其视为后续需要修复和重新验证的模块。

综合上述分析，可将当前阶段的核心结论压缩为以下表述：

`drift + bank` 构成了当前 `ours` 中最主要的有效来源，`router` 具有一定模块增益但尚未闭环证成，而 `anti-overlap regularization` 仍未得到当前实验结果的支持。
