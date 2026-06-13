# v8_sota_1 —— Orthogonal Soft Routing（评测期正交门控混合）

日期：2026-06-12  
基础版本：**v6_sota_2**（seen_avg=0.350 @seg18；回退 v7_1 的校准+NLL 仲裁）

## 动机
- v6_sota_3–5：soft top-k 混合在重叠 LoRA 分支（overlap_mean_cosine≈0.9）上产生破坏性干扰；
- v6_sota_4：纯硬路由无缓冲，seg3 崩溃；
- v7_sota_1：NLL 仲裁过激，seg5 早停（seen=0.197）。
- 老师建议三：在**路由权重**层做正交门控，保留 soft 缓冲同时抑制高相似分支同时获高权重。

## 本版改动（单点：评测期）
1. `core/evaluate.py`：新增 `_orthogonal_gate_blend_weights`  
   \(\tilde{w}_i \propto w_i \cdot \exp(-\lambda \sum_{j \neq i} |\cos(v_i, v_j)|)\)，对 soft top-k 权重重归一化后 `set_soft_routing`。
2. `core/methods/router.py`：配置 `orthogonal_blend: true`, `orthogonal_blend_lambda: 0.5`。
3. 配置：同 v6_sota_2 训练预算（1ep/batch=2）；**禁用** v7 的 `prototype_calibration` / `nll_arbitration`；保留轨迹早停。

## Novelty
- O-LoRA / LoRA-MoE：参数或子空间正交，无评测混合门控；
- DEMix：困惑度路由，无 LoRA 相似度惩罚；
- **我们**：CL frozen-specialized bank 上首个 **相似度门控 soft blend**，由 v6 混合失败实证动机。

## 判据
- seg3 seen ≥ 0.20；seg4 ≥ 0.29（v6_2 轨迹 -0.05）
- seg18 seen > 0.35（超越 v6_2/v4_39）
- orthogonal_blend_count 随分支数上升；oracle 利用率改善

## 运行
- tmux: `v8_sota_1` | 日志: `v8_sota_1.log`
- wandb: project=lora-citb-sota, group=v8_sota
