# v8_sota5 Campaign — Cursor Agent 唤醒指令

被 `AGENT_LOOP_WAKE_CAMPAIGN` 或 `CAMPAIGN_AGENT_WAKE.flag` 唤醒时，在 `/root/autodl-tmp/Lora-code` 执行以下流程。

## 1. 必读文件

- `experiments/v8_sota5_campaign/supervisor/CAMPAIGN_STATUS.md` — 人类可读总览（完成 X/41、当前 run、段进度、错误、下一步）
- `experiments/v8_sota5_campaign/supervisor/CAMPAIGN_MONITOR_STATE.json` — 结构化状态（`pending_agent`、`pending_action`）
- `experiments/v8_sota5_campaign/supervisor/CAMPAIGN_MONITOR.log` — 监控 tick 与 AUTO_FIX 记录
- `experiments/v8_sota5_campaign/manifest.csv` — 41 条战役清单

## 2. 按 kind / pending_action 行动

| 信号 | 动作 |
|------|------|
| `kind=wake` 或 `pending_action=fix` | 诊断故障 → 修代码/脚本 → 必要时重启 tmux 串行 → 清除 `pending_agent` |
| `kind=report` 或 `reason=milestone` | 用**中文**向用户汇报进度、当前 run、segment、关键 accuracy、错误与 ETA |
| `kind=tick` | 快速健康检查；无异常则简短确认 |

## 3. 诊断清单

| 检查项 | 健康 | 异常动作 |
|--------|------|----------|
| tmux | `v8s5camp_serial` 或 `v8s5camp_priority` 存活 | manifest 未完成且无 train.py → 重启串行 |
| train.py 数量 | **恰好 1 个** campaign 训练（单 GPU） | >1 时保留最新 PID，杀掉其余 |
| segment | metrics.jsonl 持续更新 | >1h 无更新 → 查日志、重启 |
| OOM | 日志无近期 OOM | 确认串行、调 batch/config |
| 并行 tmux | 勿同时开 baselines+ours+ablation | 只保留 serial 或 queue |

**硬性禁止**：在同一 GPU 上并行多个 `train.py`；勿杀掉正在健康训练的唯一 campaign 进程。

## 4. 修复 playbook

### OOM / 多进程

```bash
bash experiments/v8_sota5_campaign/pause_all_experiments.sh   # 仅多 train 或并行 tmux 时
bash experiments/v8_sota5_campaign/tmux_run_campaign_serial.sh
```

### tmux 死亡 / 停滞

```bash
bash experiments/v8_sota5_campaign/tmux_run_campaign_serial.sh
tmux attach -t v8s5camp_serial
```

### 失败 run

- 无 `final_metrics.json` 的目录会在 serial 排队时自动重跑
- 反复失败：查 `results/logs/v8_sota5_campaign/` → 修 config/代码

## 5. 完成后

- 更新 `CAMPAIGN_MONITOR_STATE.json` 的 `notes`（可选）
- 清除 `pending_agent` / `pending_action`（问题已解决时）
- 勿删除 `CAMPAIGN_AGENT_WAKE.flag`（由 `agent_loop.sh` 管理）

## 6. 向用户汇报模板（kind=report）

1. 完成进度 X/41
2. 当前 run 与 segment 进度
3. GPU 利用率与显存
4. 近期错误（如有）
5. 预计下一步 / ETA
