# v6_sota_6 监控笔记（断点续传用）

wandb: https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-citb-sota/runs/qkd8bynz
tmux: v6_sota_6 | 日志: v6_sota_6.log | 启动: 2026-06-12 01:45
配置: epochs=3, batch=1, hard routing + prompt-NLL 仲裁（margin<0.15 时 top-3 仲裁），禁参数混合

## 判据
- 内置早停：seg≥3 且 seen_avg<0.2。
- seg3/seg4 当场分 ≥0.9/0.9 → 假设成立继续；seg4 ≤0.5 → 杀停（转 epochs=1+仲裁或换路由特征）。
- seg6/7/8 seen_avg ≥ v6_2 同期-0.05（即 ≥0.376/0.323/0.244）。
- 观察 routing 的 nll_arbitration_count/changed、oracle_agreement（v6_4 同期 0.35-0.61）。
- 预计每段 ~9-11 分钟（3ep + 仲裁开销），全程 ~3-3.5h，约 05:00 跑完。

## 参考轨迹
- v6_2 seen_avg: seg3=0.25 seg4=0.34 seg5=0.325 seg6=0.426 seg7=0.373 seg8=0.294 终点 0.350
- v6_2 当场分: seg3=1.0 seg4=1.0 seg6=0.7 seg8=0.5 seg11=0.8
- v6_5（已杀停）: seg3 curr=0.9, seg4 curr=0.2
- v6_4（早停）: seg3 curr=0.7, agree 0.35-0.61

## 逐段判定记录
（待追加）
