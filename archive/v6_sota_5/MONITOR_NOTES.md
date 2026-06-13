# v6_sota_5 监控笔记（断点续传用）

wandb: https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-citb-sota/runs/a03q3hwy
tmux: v6_sota_5 | 日志: v6_sota_5.log | 启动: 2026-06-12 00:56
配置: epochs=3, batch=1, soft blend top3@T=0.08, prototype router（其余同 v6_2）

## 判据
- 内置早停：seg≥3 且 seen_avg<0.2。
- seg3/4 当场分 ≥0.9/1.0 且 seg0-2 token_f1 ≥ v6_2（0.13/0.16/0.17）→ 继续。
- seg4 当场分 ≤0.5 → 杀停；v6_6 改 verify-then-route（低置信时 prompt-NLL 仲裁、禁参数混合），不再调预算。
- seg6-8 seen_avg 低于 v6_2 同期（0.426/0.373/0.294）0.05 以上 → 杀停同上。
- 预计每段 ~8-9 分钟（3 epochs），全程 ~3 小时，约 04:00 跑完。

## 参考轨迹
- v6_2 seen_avg: seg3=0.25 seg4=0.34 seg5=0.325 seg6=0.426 seg7=0.373 seg8=0.294 ... 终点 0.350
- v6_2 当场分: seg3=1.0 seg4=1.0 seg6=0.7 seg8=0.5 seg11=0.8 seg14-17=0.6-0.8

## 逐段判定记录
- [01:24] seg0-1：seg1 curr=0（v6_2 0.1），token_f1 0.078 偏低，早期噪声，继续观察。
- [01:41] seg3 curr=0.90 ✓；**seg4 curr=0.20 ≤0.5 → 杀停判据触发**（v6_2 同期 1.0）。seg0-2 token_f1（0.125/0.078/0.074）也低于 v6_2（0.13/0.16/0.17）。
- **v6_5 结论**：3 epochs 下参数混合破坏依旧显著（air_dialogue 分类从 1.0 跌到 0.2）。预算轴关闭：blend 破坏性随预算增长，在 3ep 已不可接受。
- [01:45] 已 tmux kill-session 杀停 v6_5。转 v6_sota_6：硬路由 + 低置信 prompt-NLL 仲裁（verify-then-route），禁参数混合，epochs=3。见 archive/v6_sota_6/。
