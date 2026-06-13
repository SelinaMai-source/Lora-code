---
failed_version: v8_sota_1
next_version: v8_sota_2
status: ready
generated_at: 2026-06-12T03:40:00Z
agent_signoff: true
---

# 失败分析：v8_sota_1 → v8_sota_2

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_1 |
| 终态 | early_stopped（轨迹早停） |
| 最后 segment | 7 |
| 触发 | `seen_avg=0.302 < floor 0.323`（v6_2 seg7=0.373 − 0.05） |

### 六项目标（seg7）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | 0.302 | ≥ 0.600 | ❌ |
| seen_avg_task_aware_score | 0.325 | ≥ 0.600 | ❌ |
| forgetting | 0.114 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.114 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.356 | ≥ 0.600 | ❌ |
| lcs_overlap_mean | 0.374 | ≥ 0.600 | ❌ |

## 2. 证据链

### 2.1 轨迹 vs v6_sota_2

| seg | v8_1 seen | v6_2 | Δ | oracle | overlap_cos |
|-----|-----------|------|---|--------|-------------|
| 3 | 0.250 | 0.250 | 0.000 | 0.59 | 0.64 |
| 4 | **0.400** | 0.340 | **+0.060** | 0.64 | 0.46 |
| 5 | 0.356 | 0.325 | +0.031 | 0.35 | 0.75 |
| 6 | 0.419 | 0.426 | −0.007 | 0.34 | 0.77 |
| 7 | **0.302** | 0.373 | **−0.071** | **0.29** | **0.76** |

**关键**：v8_1 在 seg4 **超越** v6_2（0.40 vs 0.34），说明评测期正交门控在早期多分支段有效；seg5–7 oracle 从 0.35 崩至 0.29，分支 b1 占路由 64%（seg7 eval），旧任务 seg6 从 0.7→0.2（单段遗忘 0.5）。

### 2.2 根因判定

- **主因：参数空间重叠未在训练期解耦** — `overlap_mean_cosine` 在 seg5–7 维持 0.75–0.77，评测期 `orthogonal_blend_lambda=0.5` 仅重加权、不降低分支相似度；soft top-3 混合仍注入高 cos 分支干扰。
- **次因：路由崩溃** — oracle 0.29@seg7（v6_2 同期 0.55），b1 垄断路由；正交门控未修复原型/router 训练。
- **非主因**：预算（1ep/batch=2 与 v6_2 相同）；早停本身合理（真实落后 v6_2 轨迹）。

### 2.3 日志

```
Trajectory early stopping: seen_avg_score 0.302 < baseline floor 0.323 at segment 7
```

## 3. 下一版假设（单点变更）

**基座**：v6_sota_2（**移除** v8_1 的 `orthogonal_blend` 评测门控）

**唯一变更**：训练期 **Routing-aware Orthogonal Loss**
\[
\mathcal{L}_{\text{route-ortho}} = \beta_r \sum_{i<j} p_i p_j |\cos(v_i, v_j)|
\]
其中 \(p_i\) 为当前 segment 训练路由分支占比（`branch_route_fractions`），\(v_i\) 为 LoRA 权重向量。`overlap.routing_aware_beta: 0.03`。

**机制**：在参数更新时直接惩罚「常被一起路由/共现」的高相似分支对，降低 eval 期 soft blend 的破坏性干扰（针对 v8_1 暴露的 overlap≈0.76 瓶颈），而非仅在 eval 重加权。

**成功判据**：
- seg7 seen ≥ 0.323（轨迹地板）
- seg7 oracle ≥ 0.45
- overlap_mean_cosine@seg7 < 0.70
- seg18 seen > 0.35

## 4. Novelty

- O-LoRA：子空间正交，无路由共现加权；
- v8_1 eval 门控：仅推理期，未改参数几何；
- **v8_2**：首个将 **segment 路由分布 \(p_i\)** 与 **LoRA 权重余弦** 耦合的训练正则，针对 CL-bank soft-blend 干扰链（v6_3–5 + v8_1 实证）。

## 5. 审稿风险

| 风险 | 缓解 |
|------|------|
| β_r 过强压制 active 分支 | 仅 0.03，detach 非 active 向量 |
| 与 weight ortho 重复 | 路由加权聚焦「共现对」，非全局均匀惩罚 |

## 6. 门禁

- [x] status: ready
- [x] CHANGES.md / yaml / run script（随 v8_sota_2 实现）
