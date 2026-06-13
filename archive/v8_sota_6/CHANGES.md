# v8_sota_6 —— Per-Segment Anchor Prototype Refresh

日期：2026-06-12  
失败版本：v8_sota_5（跑完全程 19 seg，SOTA 未达标；seen=0.353）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3）

## 失败结论（v8_sota_5）
- **最佳 v8**：seen=0.353≈v6/v4，task_aware=**0.404** 新高，forgetting=0.049
- seg6 峰值 seen=**0.455**，seg7 断崖至 0.350（-0.105），forgetting 飙 0.083
- 距 SOTA 0.6 仍差 +0.25；中期路由收益未守住

## 单点变更
1. `router.refresh_prototype_from_anchor_features` — EMA blend anchor 质心
2. `train.py`：每 segment 训练后对 **unfrozen** 分支做 anchor 原型刷新
3. 配置：`segment_anchor_prototype_refresh: true`，`anchor_prototype_refresh_beta: 0.25`

## Novelty
spawn-sync（出生锚定）+ 段内多遍 EMA + **段末 anchor 重同步** 三级原型维护链。

## 运行
- tmux: `v8_sota_6` | 日志: `v8_sota_6.log`
