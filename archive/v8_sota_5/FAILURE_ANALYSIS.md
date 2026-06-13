---
failed_version: v8_sota_4
next_version: v8_sota_5
status: ready
generated_at: 2026-06-12T03:16:21Z
agent_signoff: true
---
# 失败分析：v8_sota_4 → v8_sota_5

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_4 |
| 终态 | early_stopped @ seg6 |
| seen_avg | 0.338（地板 0.376） |
| oracle | 0.440 |

## 2. 证据链

### 2.1 vs v6_sota_2 / v8_1–3

| seg | v8_4 | v6_2 | v8_3 | oracle(v8_4) |
|-----|------|------|------|--------------|
| 4 | 0.380 | 0.340 | 0.400 | 0.623 |
| 5 | 0.331 | 0.325 | 0.369 | **0.469** |
| 6 | **0.338** | **0.426** | 0.402 | **0.440** |

- spawn-sync **打破 v8 三连 0.302 模式**（早停点前移 seg6 但 seen 更高）
- oracle seg2–5 显著优于 v8_1/2/3；seg6 overlap 0.82 仍高

### 2.3 日志

```
Spawn-sync prototype init: b1, b2, b3 (50 anchor samples each)
Trajectory early stopping: seen 0.338 < floor 0.376 at segment 6
```

## 3. 根因分析

**主因**：spawn-sync 修复冷启动后，**每 segment 仅 1 遍原型 EMA** 不足以在 4+ 分支、overlap>0.8 时维持路由精度 → seg6 seen 崩塌。

**机制**：oracle 0.44 仍低于 v6 0.53；原型在段内未充分收敛，soft blend 放大残余误路由。

## 4. 下一版假设

**基座**：v8_sota_4（保留 spawn_sync_prototype_init）

**唯一变更**：`prototype_update_steps: 3` — 同 segment 伪标签特征上重复 3 遍 EMA 原型更新

**成功判据**：
- 通过 seg6 地板（seen ≥ 0.376）
- seg7 seen ≥ 0.35；oracle seg6+ ≥ 0.50

## 5. Novelty 与风险

- **新颖点**：段内多遍无标签原型精炼，与 spawn-sync 形成「出生锚定 + 段内收敛」
- **风险**：过拟合当段伪标签噪声；步数>3 收益递减

## 6. 门禁清单

- [x] `status: ready`
- [x] CHANGES.md + yaml + run_v8_sota_5.sh
