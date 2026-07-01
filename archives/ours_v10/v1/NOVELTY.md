# NOVELTY v1 — Spectral Sparse Replay Gating (SSRG)

## 动机（Gap 驱动）

2026-06-18 gap 审计显示 **Seq-GLUE** 为最弱 benchmark（4/4 指标未达 +10%）：

- 最强 baseline **Replay LoRA** 在 seen/ta/f1 均为 **0.7625**
- Published Ours 为 **0.7125**（约 −15% vs SOTA 目标 0.8388）
- 遗忘：Replay **0.0429** vs Ours **0.10**（未达 ≤0.0386）

Replay LoRA 靠均匀 replay buffer 维持 GLUE 任务记忆；Ours 多分支路由缺少 **任务子空间选择性 replay**，导致 seen 聚合分落后。

## 方法（文献未直接组合）

**Spectral Sparse Replay Gating (SSRG)**：

1. 跨 segment 维护紧凑 replay buffer（与 Replay 类似规模）
2. 对 buffer 样本的 hidden-state 协方差做 **截断 SVD**
3. 保留解释方差 ≥ `spectral_energy_threshold` 的 top-k 谱分量（稀疏子空间）
4. 按样本在子空间上的 **投影能量** 选 replay，而非 uniform 采样
5. 与现有 **prototype router + LoRA bank** 正交：replay 在 segment 训练前注入，router 仍按例路由

与 PP 的区别：PP 扩展 prompt 参数池，不做谱门控 replay。  
与 Replay LoRA 的区别：非均匀采样 + 与多分支路由共存。  
与 LB-CL 的区别：无 Fisher 正则，而是谱稀疏子空间匹配。

## 实现

- `core/methods/ours_spectral_replay.py` — `SpectralSparseReplayGate`
- 配置块 `spectral_replay:`（`enabled`, `replay_ratio`, `spectral_top_k`, …）
- Ablation：`spectral_replay.enabled: false` 回退 published Ours

## 预期

- Seq-GLUE seen/ta/f1 向 Replay+10% 靠拢
- 遗忘通过选择性旧任务 replay 下降

## CCF-A 叙事句

> We introduce spectral-sparse replay gating that selects rehearsal examples by their energy in the dominant eigenspace of representation covariance, coupling subspace-aware memory with drift-triggered LoRA routing for continual instruction tuning.
