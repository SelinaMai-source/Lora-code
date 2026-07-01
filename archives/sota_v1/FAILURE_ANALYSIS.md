# sota-v1 失败分析（轨迹早停 @seg4）

**Run**: `paper_instrdialogpp_sota_v1_ours_s123`  
**早停时间**: 2026-06-16 00:52:00  
**触发**: `seen_avg_score 0.24 < baseline floor 0.29` @segment 4

## 轨迹（稳定 run，PID 342716）

| seg | seen | ta | f1 | oracle | PLL bonus |
|-----|------|-----|-----|--------|-----------|
| 0 | 0.70 | 0.70 | 0.90 | 1.00 | 0 |
| 1 | 0.70 | 0.70 | 0.83 | 1.00 | 0 |
| 2 | 0.20 | 0.23 | 0.33 | 1.00 | 0 |
| 3 | 0.35 | 0.38 | 0.43 | 0.65 | 0 |
| 4 | 0.24 | 0.26 | 0.28 | 0.65 | 0 |

峰值 seen（seg≥3）= **0.35** @seg3（+33% 目标 0.3153 ✅，绝对 0.6 ❌）

## 根因

1. **seg2 生成任务崩溃**（convai3）：seg1/2 eval 跌至 0，seen 从 0.70 → 0.20；触发 drift spawn **b1**。
2. **PLL 从未激活**：`oracle_pll_min_agreement=0.55`，但 oracle 在 seg3 降至 **0.65**（仍 >0.55），故 seg4 训练前未触发 PLL recalibration。
3. **seg4 风格迁移失败**（yelp）：current=0，seen 进一步跌至 0.24，跌破 v6_sota_2 地板 0.29。
4. **遗忘严重**：seg1 从 0.8→0，forgetting=0.45 @seg2。

## sota-v2 对策

- `prototype_update_steps`: 3 → **4**（加强每段 prototype 收敛）
- `oracle_pll_min_agreement`: 0.55 → **0.68**（覆盖 oracle=0.65 的路由失配区；原计划 0.50 对本次失败无效）
- `oracle_pll_bonus_steps`: 2 → **3**

## W&B

Project: `lora-sota-campaign`, run `paper_instrdialogpp_sota_v1_ours_s123`
