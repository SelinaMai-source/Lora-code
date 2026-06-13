# v8_sota_5 —— Multi-Pass Prototype EMA Per Segment

日期：2026-06-12  
失败版本：v8_sota_4（seg6 轨迹早停，seen=0.338 < floor 0.376）  
基座：**v8_sota_4**（spawn-sync prototype init）

## 失败结论（v8_sota_4）
- 优于 v8_1/2/3：seg6 seen=0.338 vs 0.302@seg7；oracle seg5–6 **0.47/0.44** vs v8 系列 ~0.35
- spawn-sync 有效（日志 b1/b2/b3 均初始化；seg2 oracle 0.78 vs v8_3 0.57）
- seg6 仍落后 v6_2：seen -0.088，overlap 0.82↑；单遍原型 EMA 在分支增多后拟合不足

## 单点变更
1. `core/methods/router.py`：`prototype_update_steps`（默认 1）
2. `core/train.py`：每 segment 重复 `prototype_update_steps` 次伪标签原型 EMA
3. 配置：`router.prototype_update_steps: 3`

## Novelty
spawn-sync 解决冷启动 + 段内多遍原型精炼，不增加 LoRA epoch 预算。

## 运行
- tmux: `v8_sota_5` | 日志: `v8_sota_5.log`
