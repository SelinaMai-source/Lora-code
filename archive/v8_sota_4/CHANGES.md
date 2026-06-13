# v8_sota_4 —— Spawn-Sync Prototype Initialization

日期：2026-06-12  
失败版本：v8_sota_3（seg7 轨迹早停，seen=0.302，与 v8_1/2 完全相同）  
基座：**v6_sota_2**（无 eval 门控、无 routing_aware_beta、无 margin_gated）

## 失败结论（v8_sota_3 及 v8 系列）
- v8_sota_1/2/3 **逐段轨迹一致**，seg7 均为 seen=0.302
- 三条均为评测期或无效训练正则（ortho detach=0），**未触及 spawn→路由冷启动**
- seg5–7 oracle 0.38→0.31（v6_2 同期 0.51→0.55）；b1 路由垄断 ~64%

## 单点变更
1. `core/methods/router.py`：`spawn_sync_prototype_init` + `init_prototype_from_anchor_features`
2. `core/train.py`：spawn 后从 drift anchor core+probe 特征质心初始化新分支原型
3. 配置：`router.spawn_sync_prototype_init: true`

## Novelty
变点检测 → 分支出生 → 原型锚定闭环：新分支在伪标签训练前即获得 drift-window 特征质心原型。

## 运行
- tmux: `v8_sota_4` | 日志: `v8_sota_4.log`
