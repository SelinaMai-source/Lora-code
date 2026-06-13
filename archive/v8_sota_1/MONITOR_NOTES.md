# v8_sota_1 监控

- 启动：2026-06-12
- tmux：`v8_sota_1`
- 早停：seen<0.2 @seg≥3；轨迹 floor = v6_sota_2[seg]-0.05

```bash
tail -1 results/runs/paper_instrdialog_ours_full_s123_v8_sota_1/metrics.jsonl | python3 -m json.tool
tail -f v8_sota_1.log
```

下一版若失败：v8_sota_2（训练期 routing-aware ortho loss）或调 lambda 0.3/0.8。
