# v6_sota_4 监控笔记（断点续传用）

wandb: https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-citb-sota/runs/cac70jyh
tmux: v6_sota_4 | 日志: v6_sota_4.log | 启动: 2026-06-11 23:47

## 判据（来自 CHANGES.md）
- seg4 当场分仍为 0 → 立即杀停，转向降 epochs/正则化方向（v6_sota_5）
- seg6-8 seen_avg 低于 v6_2 同期（seg6=0.426, seg7=0.373, seg8=0.294）0.05 以上 → 杀停，备选熵门控混合
- seg0-2 token_f1 应回到 ≥v6_2 水平（v6_2 同期 token_f1: seg0≈0.13, seg1≈0.16, seg2≈0.17；v6_3 跌到 0.095-0.146）
- 内置早停：seg≥3 且 seen_avg<0.2 自动 sys.exit

## 参考轨迹
- v6_2 seen_avg: [0.0, 0.05, 0.0, 0.25, 0.34, 0.325, 0.426, 0.373, 0.294, 0.25, 0.236, 0.217, 0.162→后段回升至 0.35]
- v6_2 当场分: seg3=1.0, seg4=1.0, seg6=0.7, seg11=0.8
- v6_3（失败版）: seg3 当场 0.9，seg4 当场 0.0（soft 混合摧毁），seg4 后早停

## 逐段判定记录
- [00:17] seg0 完成：curr=0.0（diplomacy 生成任务，v6_2/v6_3 同为 0，正常）；token_f1=0.125（v6_3 同期 0.130，v6_2 0.13 — 持平）。训练 tta=0.537 与 v6_3 一致。无异常，继续。
- [00:53] seg1-3 完成后**内置早停**（00:43 触发：seg3 seen=0.175<0.2）。seg3 当场 0.70（v6_2 1.0 / v6_3 0.9）、seg1 当场 0（v6_2 0.1）、seg2 token_f1 0.073（更差）。判定：5 epochs 下硬路由的无对冲错误同样不可行（路由原型早期数据太少，agree=0.35-0.61）。
- **v6_4 结论**：与 v6_3 合并构成"专精化-干扰权衡"证据链：5ep+soft=混合摧毁；5ep+hard=错路由摧毁。
- [00:56] 已启动 v6_sota_5（epochs=3 + soft blend，预算二分），tmux v6_sota_5，wandb run a03q3hwy。后续判定见 archive/v6_sota_5/。
