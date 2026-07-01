# sota-v1 变更摘要

**基准**：v8_sota_5 冠军配置（`configs/paper/v8_sota_5.yaml`）  
**Benchmark**：InstrDialog++ / 38 segments / seed 123  
**日期**：2026-06-15

## 创新点：Oracle PLL Router Recalibration

受通信工程 **锁相环（PLL）** 启发：当 eval 阶段 `oracle_agreement_rate` 低于阈值（路由“失锁”），下一 segment 训练前触发额外 prototype EMA 更新 pass，临时提高 EMA 响应速度（`oracle_pll_ema_override=0.72`），使 router 重新对齐分支原型。

**新颖性**：PLL 式路由重锁未见于 continual LoRA / PEFT 文献；与 O-LoRA 正交约束、Progressive Prompts 等 advanced baseline 机制正交。

## 配置变更（相对 v8_sota_5）

| 参数 | v8_sota_5 | sota-v1 |
|------|-----------|---------|
| `router.oracle_pll_recalibrate` | — | `true` |
| `router.oracle_pll_min_agreement` | — | `0.55` |
| `router.oracle_pll_bonus_steps` | — | `2` |
| `router.oracle_pll_ema_override` | — | `0.72` |
| `router.margin_filter_min_gap` | yaml 有但未加载 | **修复**：正式注册到 Router |

## 代码变更

- `core/methods/router.py`：PLL 参数 + `margin_filter_min_gap` 注册
- `core/train.py`：`_eval_oracle_agreement()` + PLL bonus prototype steps

## 动机（来自 v8s5camp 第 3 次重启轨迹）

- seg6 峰值 seen=0.47，seg10+ oracle 跌至 0.51，seen 下滑至 0.33
- 历史 v8_sota_8/14 均因 oracle cliff 终局回落
- 小步增量：不改 lr / warmup / overlap β，仅补偿 router 失锁
