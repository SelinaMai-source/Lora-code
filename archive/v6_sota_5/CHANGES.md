# v6_sota_5 —— 训练预算二分（3 epochs + soft blend）

日期：2026-06-12
基础版本：v6_sota_2（方法不变）；预算轴上对 v6_2/v6_3 做二分。

## v6_sota_4 结果（已早停）
- seg3 时 seen_avg=0.175<0.2 内置早停（v6_2 同期 0.25）。seg3 当场分 0.70（v6_2/v6_3 为 1.0/0.9），seg1 当场 0（v6_2 0.1），seg2 token_f1 0.073（比 v6_3 的 0.095 更差）。
- 结论：5 epochs 特化分支下，**硬路由的无对冲错误与参数混合的破坏二选一都不可行**：
  - v6_3（5ep+soft）：混合摧毁特化分支输出（seg4 训练 0.998/评测 0）；
  - v6_4（5ep+hard）：路由错误样本直接 0 分，早期流（原型仅来自 1-2 段数据）路由不够准，seg3 即死。
- 三元组 v6_2/v6_3/v6_4 构成论文中"专精化-干扰权衡"的完整证据链。

## 本版改动（单轴：epochs 5→3，恢复 soft blend）
- `train.epochs_per_segment: 3`（batch=1 维持）；`router.soft_routing: true` 恢复 v6_2 设置。
- 其余与 v6_2/v6_3 完全一致。动机：1 epoch 分支欠拟合封顶 0.39，5 epochs 混合破坏；3 epochs 是预算轴的下一个二分点——分支拟合显著提高（loss 曲线显示 ~0.9 token acc），混合破坏程度预计仍温和。

## Novelty 说明
本版属预算消融（无新方法）。新发现（写论文用）：冻结-特化持续学习分支库中，参数级 soft blending 的破坏性随单分支训练预算单调增长——与 soft-MoE/model-soup 文献中"混合无害/有益"的常识相反。

## 判据
- 内置早停（seg≥3 seen<0.2）。
- seg3/4 当场分 ≥0.9/1.0 且 seg0-2 token_f1 ≥ v6_2 水平 → 混合在 3 epochs 仍安全，继续；
- seg4 当场分 ≤0.5 → 混合破坏已现，杀停；v6_6 改输出空间路由机制（如低置信时 prompt-NLL 仲裁的 verify-then-route，禁参数混合），不再调预算。
- seg6-8 seen_avg 低于 v6_2 同期 0.05 以上 → 杀停同上。

## 运行信息
- tmux: v6_sota_5 | 日志 v6_sota_5.log | wandb run a03q3hwy（project lora-citb-sota, group v6_sota）
- 结果目录：results/runs/paper_instrdialog_ours_full_s123_v6_sota_5/
