# v8_sota_3 —— Margin-Gated Hybrid Eval Routing

日期：2026-06-12  
失败版本：v8_sota_2（seg7 轨迹早停，seen=0.302，与 v8_sota_1 相同）  
基座：**v6_sota_2**（无 orthogonal_blend、无 routing_aware_beta）

## 失败结论（v8_sota_2）
- 与 v8_sota_1 **逐段相同** seg7 seen=0.302；routing-aware ortho 未改变轨迹
- `train.anti_overlap_routing_loss` 全程 ≈0：损失项全 detach，无训练梯度；overlap/oracle 仍差
- seg5–7 oracle 0.38→0.31（v6_2 同期 0.51→0.55）；overlap ~0.76 并非主因（v6_2 seg7 overlap 0.81 仍更好）

## 单点变更
1. `core/methods/router.py`：`margin_gated_soft_routing`、`margin_gate_threshold`
2. `core/evaluate.py`：prototype top1-top2 margin ≥ 0.12 → hard top-1；否则 soft top-3
3. 配置：`router.margin_gated_soft_routing: true`，`margin_gate_threshold: 0.12`

## Novelty
评测期「置信则专、不确定则混」：介于 v6_4 全硬与 v8_1 全软+正交门控之间，针对 soft-blend 在高 margin 误路由时的破坏性混合。

## 运行
- tmux: `v8_sota_3` | 日志: `v8_sota_3.log`
