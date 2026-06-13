---
failed_version: v8_sota_9
status: ready
agent_signoff: true
generated_at: 2026-06-13T02:15:00Z
---
# 失败分析：v8_sota_9（早停 seg8）

## 1. 结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_9 |
| 终态 | **early_stopped @ seg8** |
| 最后 seen | **0.2944** |
| 冠军 v8_sota_5 @seg8 | **0.350** |
| 轨迹地板 seg8 | 0.328 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_9 |

### 六项目标（早停点 seg8）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | 0.2944 | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3370 | ≥ 0.6 | ❌ |
| forgetting | 0.1167 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.1063 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.3504 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.3550 | ≥ 0.6 | ❌ |

## 2. 轨迹 vs 冠军 v8_sota_5

| seg | seen (v8_9) | seen (v8_5) | Δ | oracle (v8_9) | oracle (v8_5) |
|-----|-------------|-------------|---|---------------|---------------|
| 5 | 0.431 | 0.431 | 0.000 | 0.370 | 0.444 |
| 6 | 0.426 | **0.455** | -0.029 | 0.242 | 0.341 |
| 7 | 0.335 | **0.350** | -0.015 | 0.208 | 0.436 |
| 8 | **0.294** | **0.350** | **-0.056** | **0.117** | 0.306 |

- seg5 持平；seg6 起 oracle 崩塌（0.242 vs 0.341），seg8 oracle **0.117**（v8_5 仍 0.306）
- seg7–8 断崖与 v8_sota_1/2/3 模式一致（seen≈0.30），但 v8_5 冠军已突破此 cliff

## 3. 根因

**主因**：4-pass + `prototype_ema=0.9` 在分支≥4 时**过度改写原型**，oracle 从 seg6 起持续下滑，seg7–8 路由崩溃。

**机制**：
- 4-pass × β=0.1/步 → 段内有效 EMA 强度仍高于 3-pass（β=0.2），伪标签噪声在 4 遍累积
- seg7 `router_train_acc=0.0`、seg8 `router_train_acc=0.31`；raw routing 偏 b2/b3 但决策落 b4（branch_counts 失衡）
- overlap_mean_cosine seg6–7 ≈0.76 未降；4-pass 无法解决子空间重叠，反而加速原型漂移

**证伪**：4-pass 系列（v8_8 末段回落、v8_9 seg7–8 cliff）→ **放弃 4-pass 路线**

## 4. 配置回顾

- 基座意图：v8_sota_5 + `prototype_update_steps: 4` + `prototype_ema: 0.9`
- 早停日志：`Trajectory early stopping: seen_avg_score 0.294 < baseline floor 0.328 at segment 8`
