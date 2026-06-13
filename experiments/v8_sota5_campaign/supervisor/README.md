# v8_sota5 战役监督系统

持续监控 41 条 manifest 实验进度，自动修复常见故障，并通过 Cursor agent 处理复杂问题并向用户汇报。

## 架构

```
v8s5camp_supervisor (tmux)
  └── monitor_loop.sh  ──每 120s──► monitor_tick.py
                                        ├── 健康检查 + 自动修复
                                        ├── CAMPAIGN_MONITOR.log
                                        ├── CAMPAIGN_MONITOR_STATE.json
                                        └── CAMPAIGN_AGENT_WAKE.flag（issue/milestone 时）

v8s5camp_agent_loop (tmux)
  └── agent_loop.sh  ──每 30s──► 读 flag / pending_agent
                    ──每 5min──► monitor_tick.py
                    ──每 30min──► 定期 report
                         └── stdout: AGENT_LOOP_WAKE_CAMPAIGN JSON
```

## 启动

```bash
cd /root/autodl-tmp/Lora-code

# 监控循环（120s tick，必需）
tmux new-session -d -s v8s5camp_supervisor \
  'bash experiments/v8_sota5_campaign/supervisor/monitor_loop.sh'

# Agent 唤醒循环（配合 Cursor /loop）
tmux new-session -d -s v8s5camp_agent_loop \
  'bash experiments/v8_sota5_campaign/supervisor/agent_loop.sh'
```

环境变量：

| 变量 | 默认 | 含义 |
|------|------|------|
| `CAMPAIGN_MONITOR_INTERVAL_SEC` | 120 | supervisor 监控间隔 |
| `CAMPAIGN_AGENT_POLL_SEC` | 30 | agent_loop 轮询间隔 |
| `CAMPAIGN_MONITOR_TICK_SEC` | 300 | agent_loop 内 monitor_tick 间隔 |
| `CAMPAIGN_AGENT_REPORT_SEC` | 1800 | 健康状态下定期汇报间隔 |

## 连接 tmux

```bash
tmux ls
tmux attach -t v8s5camp_supervisor    # 监控 tick 日志
tmux attach -t v8s5camp_serial         # 训练进度
tmux attach -t v8s5camp_agent_loop     # agent 唤醒 JSON 输出
```

## Cursor Agent 如何被唤醒

### 方式 1：issue flag（故障）

`monitor_tick.py` 检测到 OOM、多 train、tmux 死亡、segment 卡住等时写入  
`CAMPAIGN_AGENT_WAKE.flag`（`reason=issue`）。

`agent_loop.sh` 每 30s 读取 flag，向 stdout 打印：

```
AGENT_LOOP_WAKE_CAMPAIGN {"reason":"issue","kind":"wake","prompt":"...",...}
```

在 Cursor 中用 `/loop` skill 监控该 sentinel（regex: `^AGENT_LOOP_WAKE_CAMPAIGN`）即可自动唤醒 agent 修复。

### 方式 2：milestone / report（进度汇报）

run 完成或优先队列完成时，flag 的 `reason=milestone`；  
即使无故障，`agent_loop` 每 30 分钟也会 `--reason report` 定期汇报。

### 方式 3：手动测试

```bash
bash experiments/v8_sota5_campaign/supervisor/cursor_agent_wake.sh \
  --reason report --message "test"
```

### 方式 4：Cursor /loop 命令

```
/loop 5m Read experiments/v8_sota5_campaign/supervisor/AGENT_LOOP_PROMPT.md and CAMPAIGN_STATUS.md
```

## 脚本说明

| 脚本 | 作用 |
|------|------|
| `status_report.py` | 读 manifest、train.py、metrics.jsonl、日志 → 写 `CAMPAIGN_STATUS.md` + 更新 state |
| `monitor_tick.py` | 健康检查、自动修复、写 wake flag |
| `cursor_agent_wake.sh` | `--reason issue\|report\|milestone --message "..."` → flag + stdout JSON |
| `agent_loop.sh` | 轮询 flag、调用 monitor_tick、定期 report |
| `AGENT_LOOP_PROMPT.md` | Agent 被唤醒后的操作手册 |

## 自动修复 vs Agent

| 场景 | 自动（monitor_tick） | 需 Agent |
|------|---------------------|----------|
| >1 个 train.py | 杀多余，保留最新 | GPU 与非 campaign 冲突 |
| 并行 tmux | 杀掉并行会话 | — |
| OOM 日志 | 记 state、杀并行 tmux、写 issue flag | 根因、config 调优 |
| tmux 死亡 | 重启 serial | 重启失败 |
| segment 卡住 >1h | 写 issue flag | 查日志、重启 |
| run 完成 | milestone flag | 向用户汇报 metrics |
| 健康单 train | 清 pending | — |

## 状态文件

- **CAMPAIGN_STATUS.md** — 中文可读：完成 X/41、当前 run、段进度、错误、下一步
- **CAMPAIGN_MONITOR_STATE.json** — `manifest`、`current_run`、`pending_agent`、`issues`
- **CAMPAIGN_MONITOR.log** — tick 摘要
- **agent_wake.log** — agent_loop 发射记录

## 手动单次检查

```bash
python3 experiments/v8_sota5_campaign/supervisor/monitor_tick.py
python3 experiments/v8_sota5_campaign/supervisor/status_report.py
cat experiments/v8_sota5_campaign/supervisor/CAMPAIGN_STATUS.md
```

## 用户如何收到汇报

1. 在 Cursor 中启用 `/loop` 监控 `v8s5camp_agent_loop` tmux 的 `AGENT_LOOP_WAKE_CAMPAIGN` 输出
2. Agent 被唤醒后按 `AGENT_LOOP_PROMPT.md` 阅读 `CAMPAIGN_STATUS.md` 并用中文回复用户
3. 每 30 分钟自动 report（即使无故障）
4. run 完成 / 优先队列完成时 milestone 唤醒

## 与旧 SOTA 监督的关系

| 旧 (`scripts/sota_*`) | 新 (本目录) |
|----------------------|-------------|
| `SOTA_AGENT_WAKE.flag` | `CAMPAIGN_AGENT_WAKE.flag` |
| `AGENT_LOOP_WAKE_SOTA` | `AGENT_LOOP_WAKE_CAMPAIGN` |
| `sota_agent_loop` tmux | `v8s5camp_agent_loop` tmux |

两套可并存；本系统只管理 manifest 战役（`*_v8s5camp`），不干预 `v8_sota_*` 单版本追逐（除非 GPU 冲突）。
