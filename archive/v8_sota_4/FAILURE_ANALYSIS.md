---
failed_version: v8_sota_3
next_version: v8_sota_4
status: ready
generated_at: 2026-06-12T01:51:58Z
agent_signoff: true
---
# 失败分析：v8_sota_3 → v8_sota_4

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_3 |
| 终态 | early_stopped |
| 最后 segment | 7 |
| 早停 | seen=0.302 < floor 0.323 |

## 2. 证据链

### 2.1 v8 系列三连败（相同轨迹）

| seg | v8_1 | v8_2 | v8_3 | v6_2 | oracle(v8_3) |
|-----|------|------|------|------|--------------|
| 4 | 0.400 | 0.380 | 0.400 | 0.340 | 0.652 |
| 5 | 0.356 | 0.367 | 0.369 | 0.325 | 0.370 |
| 6 | 0.419 | 0.402 | 0.402 | 0.426 | 0.352 |
| 7 | **0.302** | **0.302** | **0.302** | **0.373** | 0.307 |

- v8_1：eval orthogonal_blend  
- v8_2：train routing-aware ortho（全程 loss=0，detach 无梯度）  
- v8_3：eval margin-gated hybrid  
→ **评测期路由策略变更无法改变 seg7 崩溃**；训练权重轨迹实质相同

### 2.2 与 v6_sota_2 分叉点

- seg2：v8 oracle=0.57 vs v6 oracle=1.0（分支增多后原型区分度差）
- seg5+：v8 领先 seen 但 oracle 暴跌；seg7 单段 seg6 遗忘 0.50（acc 0.2 vs best 0.7）
- overlap ~0.76 非充分条件（v6 seg7 overlap 0.81 仍更好）

## 3. 根因分析

**主因**：新 spawn 分支在伪标签训练前**无原型** → 路由默认偏向旧 dominant 分支（b1 ~64%）→ oracle 雪崩 → seg7 遗忘尖峰。

**机制**：v8_1/2/3 均在 eval/无效训练侧打转，未修复「变点 spawn → 原型冷启动」断链。评测门控只改混合权重，无法让新分支可被正确路由。

## 4. 下一版假设

**基座**：v6_sota_2

**唯一变更**：spawn-sync prototype init — drift 触发 spawn 时，用当前 anchor set（core+probe）在新分支 adapter 下的特征质心初始化原型。

**成功判据**：
- seg7 seen ≥ 0.35，oracle ≥ 0.45
- seg5+ oracle 不低于 v6_2 同期
- 日志可见 `Spawn-sync prototype init`

## 5. Novelty 与审稿风险

- **新颖点**：Drift-Spawning Bank 与 Prototype Router 的状态机闭环（spawn 即锚定）
- **风险**：质心来自未训练新 adapter，可能噪声大；依赖 anchor 代表性

## 6. 门禁清单

- [x] `status: ready`
- [x] `CHANGES.md` + yaml + `run_v8_sota_4.sh`
