# v8_sota_12 —— v8_sota_5 Champion Exact Replica (Pipeline Verification)

日期：2026-06-13  
失败版本：v8_sota_11（seg4 灾难性早停，seen=0.22 < 冠军 v8_5=0.353）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_11）
- `router_warmup_segments=2` 证伪：seg4 seen=0.22，seg3 acc 1.0→0.1，forgetting=0.225
- 比 v8_1/2/3 cliff（~0.30@seg7）更早、更惨
- seg0–2 100% fallback，原型路由未在分支增多期充分学习

## 单点变更
- **无配置变更** — 与 v8_sota_5 yaml 完全一致（warmup=1, beta=0.05, 3-pass, lr=0.008）
- 仅 `run_name` / wandb tags 更新为 v8_sota_12

## 假设
v11 灾难性失败可能由 router_warmup=2 引起；精确复刻 v8_5 验证 pipeline 能否复现 seen=0.353。复现成功后再探索 router lr 或 segment-boundary prototype snapshot。

## 成功判据
- seg5 seen≥0.40；seg7 seen≥0.35；终局 seen≥0.35

## 运行
- tmux: `v8_sota_12` | 日志: `v8_sota_12.log` | seed=123 | wandb group=v8_sota
