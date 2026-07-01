# lora_run_v10 Strict Alignment — 长期后台 Agent 监督

持续监控 **strict paper 复现**（CITB 闭环 + gap-repair），自动修复常见故障，并通过 Cursor `/loop` 唤醒聊天 Agent 处理复杂问题。

## 架构

```
lora_strict_supervisor (tmux, 每 180s)
  └── monitor_loop.sh → monitor_tick.py
                            ├── 刷新 strict tracker / STRICT_STATUS.md
                            ├── 重启死掉的 citb/ct0 tmux
                            ├── 检测 CITB 日志 Traceback/OOM → issue flag
                            └── STRICT_MONITOR_STATE.json

lora_strict_agent_loop (tmux, 每 60s)
  └── agent_loop.sh → 读 flag / pending_agent → stdout:
        AGENT_LOOP_WAKE_STRICT {"prompt":"...", "kind":"wake|report", ...}
```

## 启动

```bash
cd /root/autodl-tmp/Lora-code
chmod +x experiments/lora_strict_campaign/supervisor/*.sh
bash experiments/lora_strict_campaign/supervisor/start_supervisor.sh
```

环境变量：

| 变量 | 默认 | 含义 |
|------|------|------|
| `STRICT_MONITOR_INTERVAL_SEC` | 180 | supervisor tick 间隔 |
| `STRICT_AGENT_POLL_SEC` | 60 | agent_loop 轮询 |
| `STRICT_AGENT_REPORT_SEC` | 1800 | 定期中文汇报间隔 |

## 连接 Cursor Agent（推荐）

在 Cursor 聊天中说：

```
/loop 监控 tmux lora_strict_agent_loop 的 stdout，regex ^AGENT_LOOP_WAKE_STRICT。
被唤醒后阅读 experiments/lora_strict_campaign/supervisor/AGENT_LOOP_PROMPT.md、
STRICT_STATUS.md、STRICT_MONITOR_STATE.json，
按 prompt 修理 strict 缺口、推进 CITB paper 对齐，并用中文向用户汇报。
```

或固定心跳：

```
/loop 30m 阅读 experiments/lora_strict_campaign/supervisor/STRICT_STATUS.md，
继续 strict paper 对齐工作（CITB + gap-repair）。
```

## 工作目标（写入 AGENT_LOOP_PROMPT.md）

1. CITB Sequential/Replay × InstrDialog 与 paper 数值对齐（单 seed 全量 → 对比 → rerun）
2. 其余 baseline bridge / 资产 / preflight
3. `strict_cells` 从 0 增长；不把 diagnostic 标 strict

## 状态文件

- `STRICT_STATUS.md` — 人类可读总览
- `STRICT_MONITOR_STATE.json` — `pending_agent`、`strict_alignment`、`citb`
- `STRICT_MONITOR.log` — tick 日志
- `agent_wake.log` — agent_loop 发射记录

## 与现有 tmux 的关系

本系统**不抢占**正在跑的 `continual_instruct_tuning.py`；只补 guardian（`citb_replay_monitor`、`ct0_download`）并在 GPU 空闲时提示 Agent 排队下一 rerun。

可与 `citb_post_citb_supervisor`、`lora_run_v10_monitor` 并存。

## 完全无人值守（可选）

- 安装 [Cursor CLI](https://cursor.com/docs/cli) 后可用 `cursor-agent` 在 tmux 里直接跑 prompt（本机曾尝试自动安装）。
- 或用 [Cursor SDK](https://cursor.com/docs/sdk/python)（`cursor-sdk`）写 Python 调度器，需 `CURSOR_API_KEY`。

聊天 Agent + `/loop` 是 IDE 内最稳妥的长期方案：shell 负责盯盘与唤醒，Agent 负责修代码与决策。
