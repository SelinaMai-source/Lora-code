# SOTA Progress — InstrDialog Ours (seed s123)

**最后更新**：2026-06-13  
**当前运行**：v8_sota_15  
**tmux 会话**：`v8_sota_15` + `sota_monitor` + `sota_agent_loop`  
**冠军版本**：**v8_sota_5**（seen=0.353，task_aware=0.404）  
**wandb**：https://wandb.ai/sheungyingmai-the-university-of-hong-kong/lora-citb-sota (group: v8_sota, run: v8_sota_15)

---

<!-- LIVE_STATUS_START -->
## Live Status（自动监控）

| 项 | 值 |
|---|---|
| **最后检查** | 2026-06-13 13:15:01 UTC |
| **监控 tmux** | `sota_monitor` |
| **训练 tmux** | `v8_sota_15` |
| **状态** | running |
| **workflow** | `—` |
| **当前 segment** | 2 |
| **seen_avg** | 0.0333 |
| **task_aware** | 0.0333 |
| **forgetting** | 0.0000 |
| **oracle_agree** | 0.7755102040816326 |
| **轨迹地板 (seg≥3)** | — |
| **下一动作** | monitor v8_sota_15 (seg 2) |

### 距 SOTA 目标差距（基于最新指标）
| 指标 | 当前 | 目标 | 达标 |
|------|------|------|------|
| seen_avg | 0.0333 | 0.6 | ❌ |
| task_aware | 0.0333 | 0.6 | ❌ |
| forgetting | 0.0000 | 0.0333 | ✅ |
| ta_forgetting | 0.0000 | 0.077 | ✅ |
| token_f1 | 0.2095 | 0.6 | ❌ |
| lcs | 0.2376 | 0.6 | ❌ |
<!-- LIVE_STATUS_END -->

## Best Results Summary（全版本终局对比）

| 版本 | 状态 | seg | seen | task_aware | forget | ta_forget | token_f1 | lcs | 达标 |
|------|------|-----|------|------------|--------|-----------|----------|-----|------|
| **v8_sota_5** | **完成** | 18 | **0.353** | **0.404** | **0.049** | **0.017** | 0.419 | 0.431 | 1/6 |
| v8_sota_8 | 完成 | 18 | 0.352 | 0.404 | 0.044 | 0.011 | 0.428 | 0.438 | 1/6 |
| v4_sota_39 | 完成 | 18 | 0.352 | 0.383 | 0.050 | 0.039 | **0.435** | **0.475** | 1/6 |
| v6_sota_2 | 完成 | 18 | 0.350 | 0.386 | 0.057 | 0.042 | 0.422 | 0.445 | 1/6 |
| v8_sota_4 | 早停 | 6 | 0.338 | 0.376 | 0.169 | 0.142 | 0.392 | 0.415 | 0/6 |
| v8_sota_1/2/3 | 早停 | 7 | 0.302 | 0.325 | ~0.11 | ~0.10 | ~0.35 | ~0.37 | 0/6 |
| v8_sota_6 | 早停 | 15 | 0.264 | 0.306 | 0.091 | 0.079 | 0.401 | 0.441 | 0/6 |
| v8_sota_12 | 完成 | 18 | 0.347 | 0.381 | 0.056 | 0.042 | 0.423 | 0.441 | 1/6 |

**分项冠军**：seen/task_aware → **v8_sota_5**；forgetting/ta_forget/token_f1/lcs（v8_8 末段）→ v8_sota_8 部分更优但未夺冠  
**综合冠军**：**v8_sota_5**（seen 最高）  
**距 SOTA 目标**：seen +0.247、task_aware +0.196、token_f1 +0.181、lcs +0.169；forgetting 仍超 0.033

---

## SOTA 目标（19 segment 终局，全部同时满足）

| # | 指标 | 目标 | 当前最佳 (v8_sota_5 @seg18) | 差距 |
|---|------|------|---------------------------|------|
| 1 | seen_avg_score | ≥ 0.600 | 0.353 | +0.247 |
| 2 | seen_avg_task_aware_score | ≥ 0.600 | 0.404 | +0.196 |
| 3 | forgetting | ≤ 0.0333 | 0.049 | -0.016 |
| 4 | task_aware_forgetting | ≤ 0.077 | 0.017 | ✅ |
| 5 | token_f1_mean | ≥ 0.600 | 0.419 | +0.181 |
| 6 | lcs_overlap_mean | ≥ 0.600 | 0.431 | +0.169 |

---

## v8_sota_8 结果（19 seg 完成，未夺冠）

**假设**：v8_sota_5 + `prototype_update_steps=4`

| 指标 | v8_sota_8 | v8_sota_5 | SOTA 目标 |
|------|-----------|-----------|-----------|
| seen | 0.3518 | **0.3526** | ≥0.6 |
| task_aware | 0.4044 | 0.4044 | ≥0.6 |
| forgetting | **0.0444** | 0.0491 | ≤0.0333 |
| ta_forgetting | **0.0111** | 0.0167 | ≤0.077 ✅ |
| token_f1 | **0.4276** | 0.4191 | ≥0.6 |
| lcs | **0.4385** | 0.4310 | ≥0.6 |

- 中段峰值 seg6 **0.483**（v8_5: 0.455）；seg16–17 ~0.39；终局回落至 0.352
- 失败分析：`archive/v8_sota_8/FAILURE_ANALYSIS.md`

---

## 版本历史

| 版本 | seen@18 | 状态 | 教训 |
|------|---------|------|------|
| v4_sota_39 | 0.352 | 完成 | 历史最佳 |
| v6_sota_2 | 0.350 | 完成 | 最佳 v6；原型路由 |
| v7_sota_1 | 0.197@seg5 | 早停 | NLL+校准过激 |
| v8_sota_1 | 0.302@seg7 | 轨迹早停 | eval 门控不足 |
| v8_sota_2 | 0.302@seg7 | 轨迹早停 | routing ortho 无梯度 |
| v8_sota_3 | 0.302@seg7 | 轨迹早停 | margin-gated 无效 |
| v8_sota_4 | 0.338@seg6 | 轨迹早停 | spawn-sync 有效 |
| v8_sota_5 | **0.353** | 完成 | 最佳 v8；ta 新高 |
| v8_sota_6 | 0.264@seg15 | 早停 | anchor refresh 证伪 |
| v8_sota_7 | 0.319@seg8 | 早停 | 硬路由证伪 |
| v8_sota_8 | 0.352 | 完成 | 4-pass 中段强、终局回落 |
| v8_sota_9 | 0.294@seg8 | 早停 | 4-pass+ema=0.9 seg7-8 cliff |
| v8_sota_10 | 0.348@seg9 | 早停 | overlap β=0.07 证伪 |
| v8_sota_11 | 0.220@seg4 | 早停 | router_warmup=2 灾难性 |
| v8_sota_12 | 0.347@seg18 | 完成 | pipeline 复刻未夺冠（-0.007 seen） |
| v8_sota_13 | 0.341@seg18 | 完成 | router lr 0.006 证伪；seg5 门禁失败 |
| v8_sota_14 | 0.321@seg7 | 早停 | router lr 0.010 证伪；seg7 cliff |
| **v8_sota_15** | — | **运行中** | v8_5 + prototype_ema 0.85 |

---

## v8_sota_11 结果（seg4 灾难性早停）

**假设**：v8_sota_5 + `router_warmup_segments: 2`

| 指标 | v8_sota_11 @seg4 | v8_sota_5 @seg5 |
|------|------------------|-----------------|
| seen | **0.220** | **0.420** |
| forgetting | 0.225 | 0.0 |
| oracle | 0.768 | ~0.75 |

- seg3 acc 1.0→0.1 灾难性遗忘；比 cliff runs 更早更惨
- 失败分析：`archive/v8_sota_11/FAILURE_ANALYSIS.md` → `archive/v8_sota_12/FAILURE_ANALYSIS.md`

---

## v8_sota_12 结果（seg18 完成，未夺冠）

**假设**：v8_sota_5 冠军精确复刻（零配置变更），pipeline 验证

| 指标 | v8_sota_12 | v8_sota_5 | SOTA 目标 |
|------|------------|-----------|-----------|
| seen | 0.3465 | **0.3526** | ≥0.6 |
| task_aware | 0.3807 | **0.4044** | ≥0.6 |
| forgetting | 0.0556 | **0.0491** | ≤0.0333 |
| ta_forgetting | 0.0417 | **0.0167** | ≤0.077 ✅ |
| token_f1 | **0.4229** | 0.4191 | ≥0.6 |
| lcs | **0.4408** | 0.4310 | ≥0.6 |

- 非灾难性；seg17 seen=0.366 接近冠军；末段 oracle=0.393 < 0.417
- 失败分析：`archive/v8_sota_13/FAILURE_ANALYSIS.md`

---

## v8_sota_13 结果（seg18 完成，未夺冠）

**假设**：v8_sota_5 + `router.learning_rate: 0.006`（保守路由学习率）

| 指标 | v8_sota_13 | v8_sota_5 | SOTA 目标 |
|------|------------|-----------|-----------|
| seen | 0.3412 | **0.3526** | ≥0.6 |
| task_aware | 0.3807 | **0.4044** | ≥0.6 |
| forgetting | 0.0509 | **0.0491** | ≤0.0333 |
| ta_forgetting | 0.0417 | **0.0167** | ≤0.077 ✅ |
| token_f1 | 0.4194 | 0.4191 | ≥0.6 |
| lcs | 0.4394 | 0.4310 | ≥0.6 |

- seg5 seen=0.383（门禁 0.40 失败）；低于 v12（0.347）与 v8_5
- 失败分析：`archive/v8_sota_14/FAILURE_ANALYSIS.md`

---

## v8_sota_14 结果（seg7 轨迹早停）

**假设**：v8_sota_5 + `router.learning_rate: 0.010`（自 0.008 上调 25%）

| 指标 | v8_sota_14 @seg7 | v8_sota_5 @seg7 |
|------|------------------|-----------------|
| seen | **0.321** | **0.350** |
| task_aware | 0.356 | 0.373 |
| oracle | 0.446 | 0.436 |
| forgetting | 0.090 | — |

- seg5 seen=0.350（门禁 0.40 失败）；seg5 oracle=0.481 > 冠军 0.444 但 seen 更差 → overshoot
- seg7 acc=0.0 cliff 早停（seen=0.321 < 地板 0.323）
- 失败分析：`archive/v8_sota_15/FAILURE_ANALYSIS.md`

---

## 当前实验：v8_sota_15

**假设**：v8_sota_5 + `router.prototype_ema: 0.85`（自 0.8 上调），阻尼原型 overshoot、稳定 seg5–7

| 项目 | 值 |
|------|-----|
| 配置 | `configs/paper/v8_sota_15.yaml` |
| 日志 | `v8_sota_15.log` |
| 结果 | `results/runs/paper_instrdialog_ours_full_s123_v8_sota_15/` |
| 归档 | `archive/v8_sota_15/` |

---

## v8_sota_9 结果（seg8 轨迹早停）

**假设**：v8_sota_5 + 4-pass + `prototype_ema=0.9`

| 指标 | v8_sota_9 @seg8 | v8_sota_5 @seg8 |
|------|-----------------|-----------------|
| seen | 0.294 | **0.350** |
| task_aware | 0.337 | 0.372 |
| oracle | 0.117 | 0.306 |
| forgetting | 0.117 | — |

- seg7–8 oracle 崩塌（0.208→0.117），复现 v8_1/2/3 cliff 模式
- 失败分析：`archive/v8_sota_9/FAILURE_ANALYSIS.md` → `archive/v8_sota_10/FAILURE_ANALYSIS.md`

---

## Iteration Protocol（强制）

每个新版本 **必须** 经过以下闭环（监控 `SOTA_MONITOR_STATE.json` 强制执行）：

| 阶段 | `pending_action` | 产出 | 门禁 |
|------|------------------|------|------|
| 1. 失败分析 | `failure_analysis` | `archive/v{N+1}/FAILURE_ANALYSIS.md` | 自动草稿 + **Agent 审阅**，frontmatter `status: ready` |
| 2. 实现 | `implement` | yaml + run.sh + `CHANGES.md` | Agent 单点增量实现 |
| 3. 启动 | `launch` | tmux + wandb | 仅当分析 ready 且实现文件齐全 |

**禁止**：监控器在无 `FAILURE_ANALYSIS.md (status: ready)` 时盲目 launch 下一版。

### 相关文件
- 模板：`archive/TEMPLATE_FAILURE_ANALYSIS.md`
- 分析生成：`python3 scripts/sota_failure_analysis.py --failed vX --next vY`
- 监控：`scripts/sota_monitor_loop.sh` → `scripts/sota_monitor_tick.py`
- 状态：`SOTA_MONITOR_STATE.json` / `SOTA_MONITOR.log`
- 规划：`文档记录/老师建议与下一版规划.md`

**勿杀**：健康中的 `v8_sota_*` 训练 tmux 与 `sota_monitor`。
