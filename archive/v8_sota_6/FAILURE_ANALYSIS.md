---
failed_version: v8_sota_5
next_version: v8_sota_6
status: ready
generated_at: 2026-06-12T05:49:00Z
agent_signoff: true
---
# 失败分析：v8_sota_5 → v8_sota_6

## 1. 结果摘要（SOTA 未达标但最佳 v8）

| 指标 | v8_5 | 目标 | v6_2 | v4_39 |
|------|------|------|------|-------|
| seen_avg | **0.353** | ≥0.6 | 0.350 | 0.352 |
| task_aware | **0.404** | ≥0.6 | 0.386 | 0.383 |
| forgetting | 0.049 | ≤0.033 | 0.057 | 0.050 |
| token_f1 | 0.419 | ≥0.6 | 0.422 | 0.435 |
| lcs | 0.431 | ≥0.6 | 0.445 | 0.475 |

## 2. 关键轨迹

| seg | seen(v8_5) | seen(v6) | oracle(v8_5) |
|-----|------------|----------|--------------|
| 5 | **0.431** | 0.325 | 0.444 |
| 6 | **0.455** | 0.426 | 0.341 |
| 7 | 0.350 | 0.373 | 0.436 |
| 18 | 0.353 | 0.350 | 0.417 |

- seg6 历史峰值 0.455，seg7 **-0.105 断崖**（forgetting 0.083）
- 终局收敛至 v6 水平，未突破 0.4 平台

## 3. 根因

**主因**：spawn-sync + 3-pass 伪标签 EMA 提升早期 seen，但**段间原型与 drift anchor 脱节** → seg7+ 路由失稳，中期收益回吐。

**机制**：仅 spawn 时 anchor 初始化；流式漂移后原型未重同步，soft blend 放大残余误路由。

## 4. 下一版假设

**基座**：v8_sota_5（保留 spawn-sync + 3-pass）

**唯一变更**：每 segment 训练后，对 unfrozen 分支以 β=0.25 EMA 混入当前 anchor 特征质心

**成功判据**：
- seg7 seen ≥ 0.40（守住 seg6 峰值）
- 终局 seen ≥ 0.38，task_aware ≥ 0.42
- 向 SOTA 0.6 阶梯推进

## 5. 门禁

- [x] ready + CHANGES.md + yaml + run script
