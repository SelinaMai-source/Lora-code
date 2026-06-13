---
failed_version: v8_sota_12
next_version: v8_sota_13
status: ready
generated_at: 2026-06-13T09:30:00Z
agent_signoff: true
---
# 失败分析：v8_sota_12 → v8_sota_13

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_12 |
| 终态 | completed |
| 最后 segment | 18 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_12 |
| 早停 | 否 |

### 六项目标（终局 seg18）

| 指标 | v8_sota_12 | v8_sota_5（冠军） | SOTA 目标 | v12 达标 |
|------|------------|-------------------|-----------|----------|
| seen_avg_score | 0.3465 | **0.3526** | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3807 | **0.4044** | ≥ 0.6 | ❌ |
| forgetting | 0.0556 | **0.0491** | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.0417 | **0.0167** | ≤ 0.077 | ✅ |
| token_f1_mean | **0.4229** | 0.4191 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | **0.4408** | 0.4310 | ≥ 0.6 | ❌ |

**夺冠判定**：终局 seen 低 0.006（-1.8%），task_aware 低 0.024；token_f1/lcs 略优但综合未取代 v8_sota_5。**未夺冠**。

## 2. 证据链

### 2.1 轨迹 vs v8_sota_5（冠军）

| seg | seen (v12) | seen (v8_5) | Δ | oracle (v12) | overlap_cos |
|-----|------------|-------------|---|--------------|-------------|
| 5 | 0.381 | 0.431 | -0.050 | 0.519 | 0.694 |
| 6 | 0.390 | 0.455 | -0.065 | 0.780 | 0.695 |
| 7 | 0.331 | 0.350 | -0.019 | 0.564 | 0.791 |
| 12 | 0.274 | 0.283 | -0.009 | 0.470 | 0.794 |
| 17 | **0.366** | 0.371 | -0.005 | 0.413 | 0.871 |
| 18 | 0.346 | **0.353** | -0.007 | 0.393 | 0.866 |

- seg5–6 明显低于冠军（-0.05~-0.065），非 pipeline 灾难性退化
- seg17 接近冠军（Δ=-0.005），末段 oracle 0.393 < 冠军 0.417
- overlap 0.87 高，分支混合干扰持续

### 2.2 路由 / overlap / 训练（末段）

| 信号 | v8_sota_12 | v8_sota_5 |
|------|------------|-----------|
| oracle_agreement | 0.393 | 0.417 |
| overlap_mean_cosine | 0.866 | ~0.88 |
| router learning_rate | 0.008 | 0.008 |
| prototype_update_steps | 3 | 3 |
| num_branches | 10 | 10 |

### 2.3 日志摘录

```
（无早停；seg18 正常完成）
```

### 2.4 上一版 CHANGES 摘要

v8_sota_12：v8_sota_5 **零配置变更**精确复刻，pipeline 验证 run。

## 3. 根因分析

**主因**：pipeline 可运行但存在 **run-to-run 方差 + 晚期路由 oracle 偏低**；非 v11 式灾难，而是 seg5–6 峰值不足与末段 oracle 衰减（0.39 vs 0.42）叠加，seen 终局低 0.007。

**机制**：
- 配置完全一致仍 seen 0.346 < 0.353 → 排除单一超参错误，指向随机性/训练动态敏感性
- oracle 0.393 为天花板；router lr=0.008 在 10 分支高 overlap 下可能使原型 head 更新过快，侵蚀历史路由状态
- seg17 seen=0.366 接近冠军，说明基座配置仍有效，需 **稳定路由学习** 而非改 spawn/overlap/4-pass

**已证伪路线**（不再重复）：hard routing、anchor refresh、4-pass EMA、overlap.beta 0.07、router_warmup=2。

## 4. 下一版假设（单点变更）

**基座版本**：**v8_sota_5**（spawn-sync + 3-pass + soft routing + warmup=1 + overlap.beta=0.05）

**唯一变更**：`router.learning_rate: 0.006`（自 0.008 下调 25%）

**动机**：
- v12 CHANGES 明确下一探索点为 router lr 调整
- 更低 lr 减缓原型/phase head 步长，有望提升末段 oracle 稳定性
- 单点、可逆、不触碰已证伪的 4-pass / overlap / warmup 路线

**成功判据**：
- seg5 seen≥0.40；seg7 seen≥0.35；终局 seen≥0.353（超越 v8_sota_5）
- oracle_agreement 终局 ≥0.42

## 5. Novelty 与审稿风险

路由学习率消融，工程向微调；若有效可写入「prototype router 稳定性」讨论。风险低——单标量变更，易解释。

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_13/CHANGES.md`
- [x] `configs/paper/v8_sota_13.yaml` + `run_v8_sota_13.sh`
