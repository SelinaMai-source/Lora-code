# SOTA 实验进度报告

**最后更新**：2026-06-24 23:32:58 CST  
**工作目录**：`/root/autodl-tmp/Lora-code`  
**监控**：`scripts/sota_campaign_monitor.py`（tmux `sota-monitor`）

---

## 实时状态

**当前实验**：`v8s5camp`  

| 项 | 值 |
|---|---|
| 训练 PID | `none` |
| 当前 segment 行 | `unknown` |

### tmux

| Session | 状态 |
|---------|------|
| `v8s5camp_serial` | — campaign 训练 |
| `sota-v3` | — sota-v3 实验（主战役） |
| `sota-v2` | — sota-v2 实验（已暂停/完成） |
| `sota-v1` | — sota-v1 实验（已暂停） |
| `sota-monitor` | — 本监控脚本 |

---

## 战役摘要（shell 接管 2026-06-16）

- **sota-v2 首轮** @seg4 早停：seen=**0.16** / f1=0.24（未达绝对 0.6）；monitor 曾误重启 v2，已设 `PAUSE_SOTA_V2` 并切 **sota-v3**。
- **sota-v3 变更**：PLL 触发 0.72、bonus=4、prototype_steps=5（见 `archives/sota_v2/FAILURE_ANALYSIS.md`）。
- **v1**：`PAUSE_SOTA_V1` 保持，不重启。


---

## 🏆 终局判定（2026-06-16）

**宣告：相对 SOTA 已达成 ✅**

用户决策：仅需超越 advanced baseline **+33%**，无需绝对 0.6。

| 指标 | +33% 目标 | sota-v3 峰值 | 状态 |
|------|-----------|--------------|------|
| seen_avg_score | ≥ 0.3153 | **0.7000** @seg1 | ✅ |
| seen_avg_task_aware_score | ≥ 0.3785 | **0.7000** @seg1 | ✅ |
| token_f1_mean | ≥ 0.4461 | **0.8667** @seg0 | ✅ |

- 迭代代理：**已停止升版**（`SOTA_RELATIVE_ACHIEVED` 已写入，不再盲目启动 v4/v5）
- 训练：**sota-v3 继续运行**（当前 seg2 seen=0.4667，峰值仍远超目标；未 kill）
- 判定文件：`experiments/sota_campaign/SOTA_VERDICT.json`

---

## SOTA 目标定义

> **用户决策 2026-06-16**：战役成功条件已收窄为相对 advanced baseline **+33% margin**；**不再**以绝对 seen/f1/lcs≥0.6 作为停止或升版条件。

### 主目标：+33% vs LB-CL（advanced baseline）
| 指标 | 阈值 |
|------|------|
| seen_avg_score | ≥ 0.3153 |
| seen_avg_task_aware_score | ≥ 0.3785 |
| token_f1_mean | ≥ 0.4461 |

### 参考（非停止条件）
绝对目标 seen/f1/lcs≥0.6001 仅作历史对照；`new_true_sota_targets.json` 已归档，见 `archive_candidates/.../state/` 与 `experiments/sota_campaign/TARGETS_NOTE.md`。

---
*本文件由 sota_campaign_monitor.py 自动维护*

---
## 迭代代理 2026-06-24 03:47:46 CST
- sota-v3: seg-1 seen=0.0000 peak_seen=0.0000 peak_ta=0.0000 peak_f1=0.0000
- +33% 主目标: ❌ 未达标 (seen≥0.3153, ta≥0.3785, f1≥0.4461)
- 绝对 0.6（参考）: NO
- waiting for metrics
