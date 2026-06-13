# v8_sota_2 —— Routing-aware Orthogonal Training Loss

日期：2026-06-12  
失败版本：v8_sota_1（seg7 轨迹早停，seen=0.302 < floor 0.323）  
基座：**v6_sota_2**（移除 v8_1 的 eval `orthogonal_blend`）

## 失败结论（v8_sota_1）
- seg4 seen=0.40 > v6_2 0.34：评测期正交门控早期有效
- seg7 seen=0.302，oracle=0.29，overlap=0.76：仅 eval 重加权无法降低参数重叠；b1 路由垄断 64%

## 单点变更
1. `core/methods/overlap_loss.py`：`compute_routing_aware_orthogonal_loss` — \(\beta_r \sum_{i<j} p_i p_j |\cos(v_i,v_j)|\)
2. `core/train.py`：路由训练路径传入 `branch_route_fractions`
3. 配置：`overlap.routing_aware_beta: 0.03`；无 `orthogonal_blend`

## Novelty
训练期将 segment 路由分布与 LoRA 权重几何耦合，针对 CL-bank soft-blend 干扰（v8_1 overlap 实证）。

## 运行
- tmux: `v8_sota_2` | 日志: `v8_sota_2.log`
