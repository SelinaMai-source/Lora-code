# Ours v10 SOTA Campaign

**目标**：在 8×5 实验矩阵中，仅跑 **Ours / seed=123**，持续迭代直至全 benchmark SOTA。

## SOTA 定义

对每个 benchmark、每项核心指标，**Ours 终值**须满足：

| 指标 | 方向 | 条件 |
|------|------|------|
| `seen_avg_score` | 越高越好 | Ours ≥ max(baselines) × **1.10** |
| `seen_avg_task_aware_score` | 越高越好 | 同上 |
| `token_f1_mean` | 越高越好 | 同上 |
| `forgetting` | 越低越好 | Ours ≤ min(baselines) × **0.90** |

**Baselines**（只对比、不重跑）：Sequential、Replay、O-LoRA、LB-CL、PP、Continual-T0、LFPT5。

**数据源**：`results/tables/*_s123_segment_metrics.csv` 末行。

## Benchmarks

1. InstrDialog
2. InstrDialog++
3. TRACE
4. MultiWOZ NLG
5. Seq-GLUE（优先于 TOD37）

## 工程约定

- **W&B 项目**：`lora-ours-v10`
- **单 GPU 串行**；勿 kill 无关 LFPT5/用户进程
- **tmux**：`lora_ours_v10_train`（训练）、`lora_ours_v10_monitor`（10min 状态）
- **版本存档**：`archives/ours_v10/v{N}/` + git tag `ours_v10_v{N}` + W&B group `ours_v10_v{N}`
- **早停**：`OURS_V10_EARLY_STOP=1`，seg 3–5 对比 baseline 轨迹 × margin，不达标 **exit 42**
- **Gap 审计**：`python scripts/ours_v10_sota_gap_audit.py`

## CCF-A 审稿清单

- [ ] **问题**：多任务持续指令微调中，分支路由与 replay 如何协同抑制遗忘并提升 seen 指标？
- [ ] **方法新颖性**：每版 `NOVELTY_v{N}.md` 说明与 PP/Replay/LB-CL 的差异（可 ablation）
- [ ] **主表**：5 benchmark × 4 指标 vs 7 baselines，Ours 全格 ≥ +10%
- [ ] **统计**：seed=123 主结果；声明多 seed 为 future work 或附录
- [ ] **效率**：segment 级早停与 GPU 小时数记录
- [ ] **可复现**：config + W&B run + `archives/ours_v10/v{N}/`
- [ ] **失败分析**：早停 run 的 gap 曲线写入 `results/logs/`

## 当前版本

| 版本 | 焦点 benchmark | 假设 | 状态 |
|------|----------------|------|------|
| v1 | Seq-GLUE | SSRG 频谱稀疏 replay 门控 | 进行中 |

## 指挥脚本

```bash
bash experiments/ours_v10/supervisor/run_ours_v10_supervisor.sh
```
