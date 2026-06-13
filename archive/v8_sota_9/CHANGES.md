# v8_sota_9 —— 4-Pass Peak Retention (Higher EMA)

日期：2026-06-13  
失败版本：v8_sota_8（seg18 完成，seen=0.352 ≤ v8_5 冠军 0.353）  
基座：**v8_sota_5**（spawn-sync + soft routing + prototype_update_steps=3）

## 失败结论（v8_sota_8）
- 4-pass + ema=0.8 中段领先（seg6 seen=0.483 > v8_5 0.455；seg16–17 ~0.39）但终局 seen=0.352 未超 v8_5
- 每步 β=0.2 的 4 遍 EMA 段内过度改写原型，末段路由状态被侵蚀
- overlap_mean_cosine=0.878 与 v8_5 几乎相同；oracle=0.441 略升但未转化终局 seen

## 单点变更
- 配置：`prototype_update_steps: 4`（保留 v8_8 中段增益）
- 配置：`prototype_ema: 0.9`（0.8→0.9，β 0.2→0.1，峰值保留）

## 假设
4-pass 改善冷启动/中段拟合，但需更保守 EMA 防止多遍累积漂移；不改路由策略、不增 epoch、不碰 anchor refresh。

## 成功判据
- seg6 seen≥0.47；终局 seen≥0.36（超 v8_5）
- seg12–18 不低于 v8_5 同段 -0.01

## 运行
- tmux: `v8_sota_9` | 日志: `v8_sota_9.log` | seed=123 | wandb group=v8_sota
