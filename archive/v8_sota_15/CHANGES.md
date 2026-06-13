# v8_sota_15 —— v8_sota_5 + 原型 EMA 阻尼

日期：2026-06-13  
失败版本：v8_sota_14（seg7 早停 seen=0.321 < 冠军 0.353，router lr 0.010 证伪）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing + router lr=0.008）

## 失败结论（v8_sota_14）
- router lr 0.010 证伪：seg5 seen=0.350（-0.081 vs 冠军），seg7 cliff（acc=0.0）触发早停
- seg5 oracle=0.481 > 冠军 0.444 但 seen 更差 → 原型 overshoot / 路由-评测脱钩
- 与 v13（lr=0.006 完成未夺冠）形成 lr 双向证伪

## 单点变更
- `router.prototype_ema: 0.8 → 0.85`
- 其余与 v8_sota_5 完全一致（含 router lr=0.008）

## 假设
更高 prototype EMA 增强原型惯性，减缓 v14 式伪标签过拟合，稳定 seg5–7 峰值并避免 cliff。

## 成功判据
- seg5 seen≥0.40；seg6 seen≥0.43；seg7 seen≥0.35；终局 seen≥0.353

## 运行
- tmux: `v8_sota_15` | 日志: `v8_sota_15.log` | seed=123 | wandb group=v8_sota
