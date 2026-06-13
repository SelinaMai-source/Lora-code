# v6_sota_3 —— 训练预算协议对齐（baseline-matched budget）

日期：2026-06-11
基础版本：v6_sota_2（已跑完：seen_avg=0.350, task_aware=0.386, forgetting=0.057, task_aware_forgetting=0.042, token_f1=0.422, lcs=0.445；与历史最佳 v4_39 持平且协议干净）

## v6_sota_2 瓶颈分析（本版动机）
1. **单分支学习能力是硬上限**：最终 per-segment 细分显示 8/19 个 segment 为 BOTH_ZERO（task-agnostic 与 task-aware 都为 0），全部是自由生成类任务（diplomacy/convai3/circa/multi_woz/personachat/air_dialogue/smcalflow）。这些任务在**训练完当个 segment 时 current_score 就是 0**——不是遗忘、也不是路由问题，分支根本没学会。分类/选择类任务（personachat_choose、air_dialogue_cls、dstc3、pubmedqa、mutual、craigslist、deal_or_no_dialog）得分 0.6-1.0。
2. **训练预算与 baseline 不对等（对我们不利）**：true-fair baseline（paper_instrdialog_seq_s123_true_fair 等）用 `epochs_per_segment=5, batch_size=1`；v4/v5/v6 系列 ours 一直用 `epochs=1, batch=2`。证据：seq baseline 5 epochs 后 train answer_token_acc≈0.73，我们 1 epoch 只有≈0.42。同预算对齐既公平又直接攻击上限。
3. **路由衰减是次要瓶颈**：oracle_agreement 多分支段从 0.55 缓降至 0.37（v6_1 同期 0.15-0.21，prototype router 已大幅改善）；eval_debug 显示部分样本被路由到从未学过对话风格的分支，生成"i'm a large language model..."基模型废话——分支学得更扎实后原型分离度也会提高。

## 本版改动（仅配置，方法零改动）
- `train.epochs_per_segment`: 1 → 5
- `train.batch_size`: 2 → 1
- 与 true-fair baseline 训练协议完全一致（lr=2e-4 不变）；方法代码与 v6_sota_2 完全相同（archive/v6_sota_2/ 的 router.py/drift_detector.py/train.py）。

## 公平性自查（CCF-A 视角）
- 这是**消除对 ours 不利的预算失配**，使所有方法（ours 与全部 baseline）单 segment 训练预算相同：50 样本 × 5 epochs × batch 1。
- 不引入任何额外数据、不动评测协议；漂移检测、原型路由、anti-overlap 配置全部不变。
- 风险预案：5 epochs 可能让漂移 NLL 偏移更大（spawn 更频繁，max_branches=15 兜底）、单分支过拟合使遗忘略升（分支冻结机制限制其影响）。

## Novelty 说明
本版无新方法（协议对齐迭代）。方法 novelty 仍由 v6_sota_2 的漂移锚定原型路由承担；本版结果将作为论文主表的 ours 配置候选。

## 预期与判据
- 预期：分类任务保持 0.6-1.0，生成任务 current_score 与 token_f1/lcs 显著上升（EM 仍难全中，但短答案生成类如 circa/dstc3_answer 应该能逼近），seen_avg 显著超过 0.35。
- 早停判据：内置 seen_avg<0.2（seg≥3）；人工判据：seg4-6 的 current_score 在生成任务上若仍全 0 且 token_f1 无改善，杀停并转向生成对齐方向（输出格式约束/前缀对齐）。
- 运行时间预估：训练 5×，全程约 4-6 小时。

## 运行信息
- tmux 会话：v6_sota_3；日志：/root/autodl-tmp/Lora-code/v6_sota_3.log；启动脚本 run_v6_sota_3.sh
- wandb：project=lora-citb-sota, group=v6_sota, tags=[v6_sota_3, ours_full, prototype_router, protocol_matched_budget]
- 结果目录：results/runs/paper_instrdialog_ours_full_s123_v6_sota_3/
