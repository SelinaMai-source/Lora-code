# v8_sota_10 —— Stronger Overlap Regularization (β=0.07)

日期：2026-06-13  
失败版本：v8_sota_9（seg8 轨迹早停，seen=0.294 < 冠军 v8_5 seg8=0.350）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_9）
- 4-pass + ema=0.9 在 seg6 起 oracle 崩塌（0.242→0.117），seg7–8 cliff 复现 v8_1/2/3 模式
- 远差于 v8_5 冠军；4-pass 路线证伪

## 单点变更
- 配置：`overlap.beta: 0.07`（0.05→0.07，+40% 正交约束强度）
- 其余与 v8_sota_5 完全一致（3-pass、spawn-sync、soft routing、ema=0.8）

## 假设
seg6–7 overlap≥0.76 时加强分支分离，维持 oracle 可分离性，突破 seg7–8 routing cliff，不引入 4-pass 漂移。

## 成功判据
- seg7–8 seen≥0.35；终局 seen≥0.36

## 运行
- tmux: `v8_sota_10` | 日志: `v8_sota_10.log` | seed=123 | wandb group=v8_sota
