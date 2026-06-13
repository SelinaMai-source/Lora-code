---
failed_version: v8_sota_14
next_version: v8_sota_15
status: ready
generated_at: 2026-06-13T12:27:28Z
agent_signoff: true
---
# 失败分析：v8_sota_14 → v8_sota_15

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_14 |
| 终态 | early_stopped |
| 最后 segment | 7 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_14 |
| 早停 | 是（seg7 seen=0.321 < 地板 0.323） |

### 六项目标（早停点 seg7）

| 指标 | v8_sota_14 | v8_sota_5（冠军） | SOTA 目标 | v14 达标 |
|------|------------|-------------------|-----------|----------|
| seen_avg_score | 0.3208 | **0.350** @seg7 / **0.353** @seg18 | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3563 | 0.373 @seg7 / **0.404** @seg18 | ≥ 0.6 | ❌ |
| forgetting | 0.0905 | — | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.0905 | — | ≤ 0.077 | ❌ |
| token_f1_mean | 0.4059 | — | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.4225 | — | ≥ 0.6 | ❌ |

**夺冠判定**：seg7 seen 低 0.029（-8.3% vs 冠军同段）；seg7 当前段 acc=0.0 触发 cliff 早停。**未夺冠**。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（冠军）

| seg | seen (v14) | seen (v8_5) | Δ | oracle (v14) | oracle (v8_5) | overlap_cos |
|-----|------------|-------------|---|--------------|---------------|-------------|
| 4 | 0.380 | **0.420** | -0.040 | 0.768 | 0.652 | 0.631 |
| 5 | 0.350 | **0.431** | **-0.081** | 0.481 | 0.444 | 0.808 |
| 6 | 0.381 | **0.455** | -0.074 | 0.615 | 0.341 | 0.817 |
| 7 | **0.321** | **0.350** | **-0.029** | 0.446 | 0.436 | 0.888 |

- seg4–6 峰值段全面低于冠军，seg5 门禁失败（0.350 < 0.40）
- seg5 oracle=0.481 > v8_5=0.444 但 seen 更差 → **路由-评测脱钩**，激进 lr 使原型过拟合伪标签
- seg7 acc=0.0、forgetting=0.090 → 复现 v8_1/2/3 cliff 模式（非 v13 式末段缓降）
- overlap 0.888 高，分支混合干扰在 seg6–7 加剧

### 2.2 路由 / overlap / 训练（末段）

| 信号 | v8_sota_14 | v8_sota_5 @seg7 |
|------|------------|-----------------|
| oracle_agreement | 0.446 | 0.436 |
| overlap_mean_cosine | 0.888 | ~0.85 |
| router learning_rate | **0.010** | 0.008 |
| prototype_ema | 0.8 | 0.8 |
| prototype_update_steps | 3 | 3 |
| num_branches | 4 | ~4 |

### 2.3 日志摘录

```
[2026-06-13 20:26:11] Trajectory early stopping: seen_avg_score 0.32083333333333336 < baseline floor 0.323 at segment 7
```

### 2.4 上一版 CHANGES 摘要

v8_sota_14：v8_sota_5 + `router.learning_rate: 0.010`（自 0.008 上调 25%），假设加速 seg4–6 原型 head 收敛。

## 3. 根因分析

**主因**：**router lr 0.010 过高**，原型 head 在 seg4–5 对伪标签过拟合（oracle↑ 但 seen↓），seg6–7 原型漂移加剧混合干扰，seg7 灾难性遗忘触发轨迹早停。

**机制**：
- v14 相对 v13（lr=0.006 完成但未夺冠）走向另一极端：lr 0.010 使 prototype 更新步幅过大
- seg5 oracle 高于冠军但 seen 低 0.081 → 路由自信但选错分支，典型 overshoot
- seg7 当前段 acc=0.0 与 v8_1/2/3 cliff 一致，非 v13 式全程缓降
- overlap 0.888 + 不稳定原型 → soft blend 放大错误路由

**已证伪路线**（不再重复）：4-pass、hard routing、router_warmup、overlap.beta-only、**router lr 0.006 / 0.010 双向 retry**。

## 4. 下一版假设（单点变更）

**基座版本**：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing + warmup=1 + overlap.beta=0.05 + router lr=0.008）

**唯一变更**：`router.prototype_ema: 0.85`（自 0.8 上调，增强原型惯性）

**动机**：
- router lr 双向探索（0.006↓ / 0.010↑）均证伪；改调 prototype EMA 阻尼 overshoot
- 0.85 介于冠军 0.8 与 v9 灾难性 0.9（配 4-pass）之间，单点、可逆
- 更高 EMA 减缓伪标签驱动的原型抖动，目标稳定 seg5–7 峰值

**成功判据**：
- seg5 seen≥0.40；seg6 seen≥0.43；seg7 seen≥0.35（超越 v8_5 同段）
- 无 seg7 cliff（当前段 acc>0）；终局 seen≥0.353

## 5. Novelty 与审稿风险

prototype EMA 与 router lr 正交消融，可形成「原型路由超参敏感性」表格（lr × ema）。风险低——单标量、与 v9（ema=0.9+4-pass）明确区分。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_15/CHANGES.md`
- [x] `configs/paper/v8_sota_15.yaml` + `run_v8_sota_15.sh`
