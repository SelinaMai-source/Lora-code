# sota-v2 失败分析（轨迹早停 @seg4）

**Run**: `paper_instrdialogpp_sota_v2_ours_s123`（首轮，01:15:15 早停）  
**触发**: `seen_avg_score 0.16 < 0.2` @segment 4

## 轨迹（首轮）

| seg | seen | ta | f1 | oracle |
|-----|------|-----|-----|--------|
| 0 | 0.70 | 0.70 | 0.90 | 1.00 |
| 1 | 0.70 | 0.70 | 0.83 | 1.00 |
| 2 | 0.20 | 0.27 | 0.34 | 1.00 |
| 3 | 0.325 | 0.35 | 0.43 | 0.55 |
| 4 | 0.16 | 0.30 | 0.24 | 0.688 |

峰值 seen（seg≥3）= **0.325** @seg3（+33% ✅，绝对 0.6 ❌）

## 根因

1. **seg2 convai3 再次崩溃**（与 v1 同型），seen 0.70→0.20，spawn **b1**。
2. **PLL 仅在 seg4 训练触发一次**（prev_oracle=0.55），但 seg4 **eval 前** oracle 已回升至 **0.688 > 0.68**，后续 seg5 路由仍失配；且 seg4 yelp current=0。
3. **monitor 在 watchdog 正常早停后误重启 v2**（无 PAUSE_SOTA_V2），浪费 GPU 重跑同配置。
4. **b2 spawn @seg5 前**即早停，未给新分支机会。

## sota-v3 对策

- `oracle_pll_min_agreement`: 0.68 → **0.72**（覆盖 eval oracle=0.688 盲区）
- `oracle_pll_bonus_steps`: 3 → **4**
- `prototype_update_steps`: 4 → **5**（seg2 生成段前加强 prototype）
- 新增 `experiments/sota_campaign/PAUSE_SOTA_V2`，禁止 monitor 自动 relaunch v2
