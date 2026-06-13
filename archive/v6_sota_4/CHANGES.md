# v6_sota_4 —— 关闭评测期参数混合（specialization-aware hard routing）

日期：2026-06-11
基础版本：v6_sota_3（预算对齐版；seg4 早停，seen_avg=0.18）

## v6_sota_3 失败解剖（seg4 "训练 0.998 / 评测 0.0" 反常）
1. **不是过拟合本身**：seg4（air_dialogue_classification，标签答案约 1.7 token）train answer_token_acc=0.998，分支 b2 已掌握该任务；oracle 一致率 0.67，硬选大多数样本会选对分支。
2. **不是 task-aware 通道问题**：本仓库的 "task_aware" 是**评分方式感知**（label_accuracy vs strict_em），不是用真分支重新生成——它与 task-agnostic 用同一份路由生成，所以同样为 0。
3. **真凶 = soft routing 的参数混合**：评测时 `set_soft_routing` 把 top-3 分支按权重混合（seg4 决策置信度仅 0.586、熵 0.935，混合权重弥散）。v6_2（1 epoch）的分支接近基模型，混合无害；v6_3（5 epochs）分支高度特化，b2 与 b0/b1 的 LoRA 参数混合直接摧毁生成（分类标签都吐不对）。seg0-2 生成任务 token_f1 也从 v6_2 的 ~0.3 跌到 0.10-0.15，同一机制。
4. 结论：**专精化-干扰权衡（specialization–interference tradeoff）**——训练预算↑ → 分支特化↑ → 参数混合代价从近零变为毁灭性。这是论文可用的发现。

## 本版改动（仅一项配置）
- `router.soft_routing: true → false`：评测期改为纯硬路由（top-1 原型决策切换 adapter），其余与 v6_sota_3 完全一致（epochs=5/batch=1、prototype router、公平性修复全保留）。

## Novelty 论证
- 主方法 novelty 仍是 v6_2 的漂移锚定 NLL 验证原型路由；本版补充其使用准则：专精分支下禁用参数级 blending。与 soft-MoE/adapter-soup 文献的差别：那些工作中混合在联合训练下是良性的，而在冻结-特化的持续学习分支库里混合是破坏性的——我们提供了直接对照证据（v6_2 vs v6_3 vs v6_4 三元组）。

## 预期与早停判据
- 预期：seg3/seg4 当场分恢复 ~0.9/1.0；seg0-2 token_f1 回到 ≥v6_2 水平（~0.2-0.3）；seg6 时 seen_avg ≥ v6_2 同期（0.43）。
- 判据：内置早停（seg≥3 seen<0.2）；人工判据——seg4 当场分仍为 0 → 立即杀停（说明混合假设错误，转向降 epochs/正则化方向）；seg6-8 seen_avg 低于 v6_2 同期 0.05 以上 → 杀停。
- 风险：硬路由错误样本得 0（无 soft 对冲），路由后段衰减的影响会放大；若整体不及 v6_2，下一版上"熵门控混合"（仅低熵时混合）。

## 运行信息
- tmux 会话：v6_sota_4；日志：v6_sota_4.log；脚本 run_v6_sota_4.sh
- wandb：project=lora-citb-sota, group=v6_sota, tags=[v6_sota_4, ours_full, prototype_router, hard_routing, protocol_matched_budget]
- 结果目录：results/runs/paper_instrdialog_ours_full_s123_v6_sota_4/
