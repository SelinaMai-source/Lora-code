---
failed_version: v8_sota_8
next_version: v8_sota_9
status: ready
agent_signoff: true
---
# 失败分析：v8_sota_8 → v8_sota_9

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_8 |
| 终态 | completed |
| 最后 segment | 18 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_8 |
| 早停 | 否 |

### 六项目标（终局 seg18）

| 指标 | v8_sota_8 | v8_sota_5（冠军） | SOTA 目标 | v8_8 达标 |
|------|-----------|-------------------|-----------|-----------|
| seen_avg_score | 0.3518 | **0.3526** | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.4044 | 0.4044 | ≥ 0.6 | ❌ |
| forgetting | **0.0444** | 0.0491 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | **0.0111** | 0.0167 | ≤ 0.077 | ✅ |
| token_f1_mean | **0.4276** | 0.4191 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | **0.4385** | 0.4310 | ≥ 0.6 | ❌ |

**夺冠判定**：seen 微低于冠军（-0.0008），task_aware 持平；分项 forgetting/ta_forget/token_f1/lcs 更优，但综合仍以 seen 为主，**未取代 v8_sota_5**。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（4-pass EMA 中段强、末段回落）

| seg | seen (v8_8) | seen (v8_5) | Δ | oracle (v8_8) | overlap_cos (v8_8) |
|-----|-------------|-------------|---|---------------|-------------------|
| 5 | 0.447 | 0.431 | +0.016 | 0.630 | 0.733 |
| 6 | **0.483** | 0.455 | **+0.028** | 0.560 | 0.761 |
| 7 | 0.385 | 0.350 | +0.035 | 0.495 | 0.756 |
| 8 | 0.389 | 0.350 | +0.039 | 0.505 | 0.608 |
| 12 | 0.313 | 0.283 | +0.030 | 0.470 | 0.873 |
| 16 | 0.376 | 0.334 | +0.042 | 0.435 | 0.868 |
| 17 | **0.394** | 0.371 | +0.023 | 0.448 | 0.873 |
| 18 | 0.352 | **0.353** | -0.001 | 0.441 | 0.878 |

- seg6 峰值 **0.483**（v8_5 仅 0.455）；seg16–17 仍维持 ~0.39 局部峰
- seg12–14 深坑（0.29–0.31）后 seg16–17 回升，但 **seg18 终局跌回 0.352**，未保留中段优势

### 2.2 路由 / overlap / 训练（末段）

| 信号 | v8_sota_8 | v8_sota_5 |
|------|-----------|-----------|
| oracle_agreement | 0.441 | 0.417 |
| overlap_mean_cosine | 0.878 | 0.880 |
| prototype_update_steps | **4** | 3 |
| prototype_ema | 0.8 | 0.8 |

4-pass 未降低 overlap；oracle 略升但不足以转化终局 seen。

### 2.3 日志摘录

```
（无早停；seg18 正常完成，final_metrics.json 已写入）
```

### 2.4 上一版 CHANGES 摘要

v8_sota_8：`prototype_update_steps: 4`（v8_5 基座 + 段内第 4 遍伪标签原型 EMA，soft routing 不变）。

## 3. 根因分析

**主因**：4-pass EMA（β=0.2/步，ema=0.8）在段内**过度改写**原型，早中段拟合快、seen 冲高；随分支增至 10 路、overlap≈0.88，后续段的 4 遍累积更新把已收敛的原型拉向当前段伪标签，**侵蚀历史峰值路由状态**，终局 seen 回落。

**机制**：
- 每段 4 遍 EMA 等价于单步有效 β ≈ 1−0.8⁴ ≈ 0.59 向当段 batch_mean 靠拢，比 3-pass（≈0.49）更激进
- 冻结分支原型虽跳过更新，但 soft top-3 混合仍受高 overlap 邻居污染；活跃分支原型漂移拖累 eval blend
- seg6–8 领先证明 spawn-sync + 多遍 EMA 对冷启动有效；seg12+ 深坑与 v8_5 类似，但 v8_8 末段回升后再跌，符合「过拟合当段原型 → 遗忘旧任务」模式

**证伪**：
- 继续加至 5-pass 预期收益递减（更多段内漂移）
- 硬路由 v8_7、anchor refresh v8_6 已证伪
- overlap 未降说明单靠多遍 EMA 无法分离子空间

## 4. 下一版假设（单点变更）

**基座版本**：v8_sota_5（spawn-sync + soft routing + 3-pass 为对照）

**唯一变更**：保留 4-pass，**降低 EMA 更新强度** — `prototype_ema: 0.9`（β 0.8→0.9，每步仅 10% 向 batch 靠拢），在保留中段拟合增益的同时提高峰值保留。

**成功判据**：
- seg6 seen≥0.47 且 seg18 seen≥0.36（超 v8_5 冠军）
- seg12–18 轨迹地板不低于 v8_5 同段 -0.01

## 5. Novelty 与审稿风险

段内多遍原型 EMA 的 **β 扫描**（3-pass/4-pass × ema）是可消融超参；「更强段内拟合需匹配更保守 EMA 以防 CL 遗忘」叙事清晰。风险低。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_9/CHANGES.md`
- [x] `configs/paper/v8_sota_9.yaml` + `run_v8_sota_9.sh`
