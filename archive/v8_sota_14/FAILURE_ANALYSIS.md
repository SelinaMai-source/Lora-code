---
failed_version: v8_sota_13
next_version: v8_sota_14
status: ready
generated_at: 2026-06-13T11:47:27Z
agent_signoff: true
---
# 失败分析：v8_sota_13 → v8_sota_14

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_13 |
| 终态 | completed |
| 最后 segment | 18 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_13 |
| 早停 | 否 |

### 六项目标（终局 seg18）

| 指标 | v8_sota_13 | v8_sota_5（冠军） | SOTA 目标 | v13 达标 |
|------|------------|-------------------|-----------|----------|
| seen_avg_score | 0.3412 | **0.3526** | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3807 | **0.4044** | ≥ 0.6 | ❌ |
| forgetting | 0.0509 | **0.0491** | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.0417 | **0.0167** | ≤ 0.077 | ✅ |
| token_f1_mean | 0.4194 | 0.4191 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.4394 | 0.4310 | ≥ 0.6 | ❌ |

**夺冠判定**：终局 seen 低 0.012（-3.4%），低于 v12（0.347）与 v8_5。**未夺冠**；**seg5 门禁失败**（0.383 < 0.40）。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（冠军）

| seg | seen (v13) | seen (v8_5) | Δ | oracle (v13) | overlap_cos |
|-----|------------|-------------|---|--------------|-------------|
| 4 | 0.340 | 0.420 | -0.080 | 0.841 | 0.511 |
| 5 | **0.383** | **0.431** | **-0.048** | 0.494 | 0.726 |
| 6 | 0.379 | 0.455 | -0.076 | 0.791 | 0.726 |
| 7 | 0.331 | 0.350 | -0.019 | 0.604 | 0.811 |
| 12 | 0.276 | 0.283 | -0.007 | 0.503 | 0.816 |
| 17 | 0.360 | 0.371 | -0.011 | 0.428 | 0.883 |
| 18 | 0.341 | **0.353** | -0.012 | 0.393 | 0.878 |

- seg5 门禁未达（0.383 < 0.40）；seg4–6 全段低于冠军，峰值段损失最大
- 末段 oracle=0.393 ≈ v12，未改善；低于冠军 0.417
- overlap 0.88 高，分支混合干扰持续

### 2.2 路由 / overlap / 训练（末段）

| 信号 | v8_sota_13 | v8_sota_5 |
|------|------------|-----------|
| oracle_agreement | 0.393 | 0.417 |
| overlap_mean_cosine | 0.878 | 0.880 |
| router learning_rate | **0.006** | 0.008 |
| prototype_update_steps | 3 | 3 |
| num_branches | 10 | 10 |

### 2.3 日志摘录

```
（无早停；seg18 正常完成）
```

### 2.4 上一版 CHANGES 摘要

v8_sota_13：v8_sota_5 + `router.learning_rate: 0.006`（自 0.008 下调 25%），假设保守路由学习可稳定末段 oracle。

## 3. 根因分析

**主因**：**router lr 0.006 过低**，导致 seg4–6 原型 head 拟合不足，seg5 峰值（0.383）显著低于冠军（0.431）；保守更新未能提升末段 oracle，反而全程 seen 低于 v12/v8_5。

**机制**：
- v13 相对 v12（同配置除 lr）seen 再降 0.006 → 方向性证伪「更低 lr = 更稳路由」
- seg5 oracle=0.494 低于 v8_5 seg5=0.444，但 seen 更差 → 路由决策与 eval 分数脱钩，低 lr 使原型滞后于分支增长
- 末段 oracle 0.393 与 v12 相同 → lr 调整未触及天花板问题，但中段峰值损失已锁定劣势

**已证伪路线**（不再重复）：4-pass、hard routing、router_warmup、overlap.beta-only、**router lr 0.006 单向下调**。

## 4. 下一版假设（单点变更）

**基座版本**：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing + warmup=1 + overlap.beta=0.05）

**唯一变更**：`router.learning_rate: 0.010`（自冠军 0.008 **上调 25%**）

**动机**：
- v13 证伪保守 lr；对称探索更高 lr，加速 seg4–6 原型 head 收敛
- 单点、可逆；不触碰 4-pass / warmup / overlap 等已证伪路线
- 目标恢复 seg5≥0.40 峰值门禁

**成功判据**：
- seg5 seen≥0.40；seg6 seen≥0.43；终局 seen≥0.353（超越 v8_sota_5）
- oracle_agreement 终局 ≥0.42

## 5. Novelty 与审稿风险

路由学习率双向消融（0.006↓ / 0.010↑），工程向；若 0.010 有效可写入「prototype router lr sensitivity」讨论。风险低——单标量变更，与 v13 形成对照。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_14/CHANGES.md`
- [x] `configs/paper/v8_sota_14.yaml` + `run_v8_sota_14.sh`
