# v8_sota_14 —— v8_sota_5 + 激进路由学习率

日期：2026-06-13  
失败版本：v8_sota_13（终局 seen=0.3412 < 冠军 v8_5=0.353，seg5 门禁失败 0.383<0.40）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_13）
- router lr 0.006 证伪：seen 低于 v12（0.347）与 v8_5（0.353）
- seg5 seen=0.383（-0.048 vs 冠军），seg6=0.379（-0.076）；峰值段全面落后
- 末段 oracle=0.393 未改善

## 单点变更
- `router.learning_rate: 0.008 → 0.010`（+25%）
- 其余与 v8_sota_5 完全一致

## 假设
更高 router lr 加速 seg4–6 原型 head 收敛，恢复 seg5≥0.40 峰值门禁，进而提升终局 seen。

## 成功判据
- seg5 seen≥0.40；seg6 seen≥0.43；终局 seen≥0.353

## 运行
- tmux: `v8_sota_14` | 日志: `v8_sota_14.log` | seed=123 | wandb group=v8_sota
