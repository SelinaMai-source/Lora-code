# v8_sota_11 —— Extended Router Warmup (2 segments)

日期：2026-06-13  
失败版本：v8_sota_10（seg9 轨迹早停，seen=0.348 < 冠军 v8_5=0.353）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_10）
- overlap.beta 0.07 未超 v8_5 冠军；seg7 seen cliff 仍在
- seg9 router_train_acc=0.96 但 fallback_to_active=49/50，推理路由与训练脱节

## 单点变更
- 配置：`router.router_warmup_segments: 2`（1→2，seg0–1 强制 latest-branch）
- 其余与 v8_sota_5 完全一致（3-pass、spawn-sync、soft routing、overlap.beta=0.05）

## 假设
延后原型路由介入，让 spawn-sync + 3-pass 在前两段充分稳定，减少 seg2+ 过早路由错配。

## 成功判据
- seg7 seen≥0.35；seg9 seen≥0.36；fallback<30%@seg5+

## 运行
- tmux: `v8_sota_11` | 日志: `v8_sota_11.log` | seed=123 | wandb group=v8_sota
