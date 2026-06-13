---
failed_version: v8_sota_2
next_version: v8_sota_3
status: ready
generated_at: 2026-06-11T20:11:10Z
agent_signoff: true
---
# 失败分析：v8_sota_2 → v8_sota_3

## 1. 失败版本与结果摘要

| 项 | 值 |
|---|---|
| 版本 | v8_sota_2 |
| 终态 | early_stopped |
| 最后 segment | 7 |
| run_name | paper_instrdialog_ours_full_s123_v8_sota_2 |
| 早停 | 是 |

### 六项目标（终局/早停点）

| 指标 | 值 | 目标 | 达标 |
|------|-----|------|------|
| seen_avg_score | 0.3021 | ≥ 0.6 | ❌ |
| seen_avg_task_aware_score | 0.3250 | ≥ 0.6 | ❌ |
| forgetting | 0.1119 | ≤ 0.0333 | ❌ |
| task_aware_forgetting | 0.1000 | ≤ 0.077 | ❌ |
| token_f1_mean | 0.3470 | ≥ 0.6 | ❌ |
| lcs_overlap_mean | 0.3604 | ≥ 0.6 | ❌ |

## 2. 证据链

### 2.1 轨迹 vs v6_sota_2 / v8_sota_1

| seg | seen (v8_2) | v6_2 | v8_1 | oracle (v8_2) | overlap |
|-----|-------------|------|------|---------------|---------|
| 4 | 0.380 | 0.340 | 0.400 | 0.652 | 0.470 |
| 5 | 0.367 | 0.325 | 0.356 | 0.383 | 0.750 |
| 6 | 0.402 | 0.426 | 0.419 | 0.363 | 0.767 |
| 7 | **0.302** | **0.373** | **0.302** | 0.307 | 0.762 |

- v8_sota_1（eval 正交门控）与 v8_sota_2（训练 routing-aware ortho）在 seg7 **完全相同** seen=0.302
- v6_sota_2 seg7：seen=0.373，oracle=**0.554**，overlap=**0.807**（更高 overlap 但更好 oracle/seen）

### 2.2 routing-aware ortho 无效证据

| 信号 | 值 |
|------|-----|
| anti_overlap_routing_loss | 全程 0.0 |
| 机制 | `compute_routing_aware_orthogonal_loss` 对所有 adapter vector `detach=True`，损失无梯度回传 |
| 结论 | v8_sota_2 训练等价于 v6_sota_2 + 无效正则项 |

### 2.3 日志摘录

```
[2026-06-12 04:08:42] Trajectory early stopping: seen_avg_score 0.302 < baseline floor 0.323 at segment 7
```

## 3. 根因分析

**主因**：评测期 **soft top-3 混合在原型高 margin 时仍执行**，错误高置信路由被参数混合放大；seg5+ oracle 从 0.65 跌至 0.31，与 v6_2 分叉。

**机制**：
1. v8 系列（eval 门控 / train ortho）均未改变训练权重轨迹与 v8_1 一致 → 崩溃来自 **eval 路由策略** 而非 overlap 正则
2. overlap ~0.76 不是充分条件：v6_2 更高 overlap 仍保持 oracle ~0.55
3. v6_sota_4 证伪「全硬路由」；v8_sota_1 证伪「全软+正交门控」→ 需要 **按 margin 切换** 的混合策略

## 4. 下一版假设（单点变更）

**基座版本**：v6_sota_2（纯训练配置，无 v8_1/v8_2 附加项）

**唯一变更**：评测期 margin-gated hybrid routing
- `margin >= 0.12` → hard top-1（避免破坏性 blend）
- `margin < 0.12` → soft top-3（保留 v6_2 不确定样本缓冲）

**成功判据**：
- seg7 seen ≥ 0.35（超过 v8_1/2 的 0.302 地板）
- seg7 oracle ≥ 0.45（向 v6_2 的 0.55 靠拢）
- 不触发 seg7 轨迹早停

## 5. Novelty 与审稿风险

- **新颖点**：Task-agnostic CL bank 上「置信硬路由 / 不确定软混合」的 label-free 门控，与 v7 NLL 仲裁（低 margin 才介入）方向相反但互补
- **风险**：阈值 0.12 可能过严/过松；需 wandb 监控 `margin_gate_hard_count` 比例

## 6. 门禁清单

- [x] Agent 已将 frontmatter `status: ready`
- [x] `archive/v8_sota_3/CHANGES.md`
- [x] `configs/paper/v8_sota_3.yaml` + `run_v8_sota_3.sh`
