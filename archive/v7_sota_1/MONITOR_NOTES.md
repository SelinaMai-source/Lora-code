# v7_sota_1 监控笔记

## 启动
- 时间：2026-06-12
- tmux 会话：`v7_sota_1`
- 配置：`configs/paper/v7_sota_1.yaml`
- 日志：`v7_sota_1.log`

## 关键指标（每 segment 检查）
```bash
tail -1 results/runs/paper_instrdialog_ours_full_s123_v7_sota_1/metrics.jsonl | python3 -m json.tool
```

## 早停判据
1. 内置：seg≥3, seen_avg < 0.2
2. 轨迹：seg≥3, seen_avg < v6_sota_2[seg] - 0.05

## v6_sota_2 参考轨迹 (seen_avg)
| seg | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|-----|---|---|---|---|---|---|---|---|---|
| v6_2 | 0.00 | 0.05 | 0.00 | 0.25 | 0.34 | 0.33 | 0.43 | 0.37 | 0.38 |

| seg | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 |
|-----|---|----|----|----|----|----|----|----|----|----|
| v6_2 | 0.32 | 0.27 | 0.31 | 0.30 | 0.28 | 0.30 | 0.33 | 0.35 | 0.38 | 0.35 |

## SOTA 目标差距（终局 seg18）
| 指标 | 目标 | v6_2 最佳 | 差距 |
|------|------|-----------|------|
| seen_avg | 0.600 | 0.350 | +0.250 |
| task_aware | 0.600 | 0.386 | +0.214 |
| forgetting | ≤0.033 | 0.057 | -0.024 |
| ta_forgetting | ≤0.077 | 0.042 | OK |
| token_f1 | 0.600 | 0.422 | +0.178 |
| lcs | 0.600 | 0.445 | +0.155 |

## 下一版预案（若 v7_1 失败）
- v7_sota_2：提高 `prototype_calibration_prior` 到 20 + 训练期 margin 过滤与校准对齐
- v7_sota_3：仅 hard route + NLL 仲裁（禁用 soft）但保持 1ep
