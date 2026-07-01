# lora_run_v10 Strict Alignment — Cursor Agent 唤醒指令

被 `AGENT_LOOP_WAKE_STRICT` 或 `STRICT_AGENT_WAKE.flag` 唤醒时，在 `/root/autodl-tmp/Lora-code` 执行。

## 工作目标（长期）

1. **严格对齐 published paper**：8 methods × 5 benchmarks（TOD37 已删，用 Seq-GLUE）；`strict_cells` 尽可能多闭合。
2. **CITB Sequential/Replay × InstrDialog**（最高优先）：official runner 全量单 seed → collect → 与 paper Table 1 对比 → 不一致则诊断并 rerun（Stage-1 / Stage-2 / seed515 等），直到 within tolerance 或记录不可修复 blocker。
3. **其余 baseline gap-repair**（GPU 空闲时 CPU 并行）：O-LoRA / PP / Continual-T0 / LFPT5 bridge、CT0 下载、LB-CL faithful port 搜索。
4. **不把 diagnostic run 标为 strict**；更新 `results/tables/lora_run_v10_strict_alignment_tracker.csv`。

## 1. 必读文件

- `experiments/lora_strict_campaign/supervisor/STRICT_STATUS.md`
- `experiments/lora_strict_campaign/supervisor/STRICT_MONITOR_STATE.json`
- `experiments/lora_strict_campaign/supervisor/STRICT_MONITOR.log`
- `results/logs/citb/post_citb_supervisor_state.json`
- `results/tables/citb_stage2_mismatch_diagnosis.json`
- `results/tables/lora_run_v10_strict_alignment_summary.json`
- `docs/lora_run_v10_strict_alignment_report.md`

## 2. 按 kind / pending_action 行动

| 信号 | 动作 |
|------|------|
| `kind=wake` 或 `pending_action=fix` | 诊断故障 → 修脚本/依赖 → 重启 tmux 队列 → 清 `pending_agent` |
| `kind=report` 或 `reason=milestone` | **中文**汇报 strict_cells、CITB paper 对比、当前 GPU 任务、blocker |
| `kind=tick` | 快速确认 supervisor 存活；无异常则简短确认 |

## 3. CITB 修复顺序（paper 仍不符时）

1. 读 `citb_instrdialog_paper_comparison.json` 与 `citb_stage2_mismatch_diagnosis.json`
2. 若 Stage-2 全 seed 仍 AR << paper → **Stage-1 paper seed rerun**（`run_stage1_paper_seed227_rerun.sh` 等）
3. Stage-1 完成 → `run_stage2_paper_seed227_rerun_queue.sh` 或 seed515 队列
4. 每次完成 → `collect_ft_instr_metrics_only.sh` + `parse_citb_official_results.py --seed <N>`
5. 仍不符 → 审计 checkpoint、early-stop、metric parser、数据 split；写 diagnosis JSON

## 4. 硬性约束

- **单 GPU 训练**：勿与正在跑的 `continual_instruct_tuning.py` 抢 GPU
- Proxy：`http://127.0.0.1:7890`，`unset ALL_PROXY`
- 不 git commit 除非用户明确要求

## 5. 向用户汇报模板（kind=report）

1. `strict_cells` / near_strict / blocked 数量
2. CITB FT/Replay AR vs paper
3. 当前 tmux / GPU 进程
4. 本轮 fix 或下一 rerun
5. 仍 blocked 的 method×benchmark（一句话原因）
