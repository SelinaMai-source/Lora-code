# v8_sota_13 —— v8_sota_5 + 保守路由学习率

日期：2026-06-13  
失败版本：v8_sota_12（终局 seen=0.3465 < 冠军 v8_5=0.353，pipeline 复刻未夺冠）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_12）
- 零配置复刻 v8_5，终局 seen=0.3465（-0.007），非灾难性
- seg5–6 峰值不足；末段 oracle=0.393 < 冠军 0.417
- pipeline 可用，问题在路由学习动态/方差

## 单点变更
- `router.learning_rate: 0.008 → 0.006`（-25%）
- 其余与 v8_sota_5 完全一致

## 假设
较低 router lr 减缓原型 head 更新，在 10 分支高 overlap 场景下稳定末段 oracle，提升 seen 终局。

## 成功判据
- seg5 seen≥0.40；seg7 seen≥0.35；终局 seen≥0.353

## 运行
- tmux: `v8_sota_13` | 日志: `v8_sota_13.log` | seed=123 | wandb group=v8_sota
