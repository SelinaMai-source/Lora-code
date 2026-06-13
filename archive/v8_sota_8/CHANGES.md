# v8_sota_8 —— 4-Pass Prototype EMA Per Segment

日期：2026-06-12  
失败版本：v8_sota_7（seg8 轨迹早停，seen=0.319）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3 + soft routing）

## 失败结论（v8_sota_7）
- 硬路由证伪：seg8 seen=0.319 < v8_5 地板 0.328，oracle 0.30
- seg4–5 曾领先 v6_2，seg6+ 崩盘；硬 top-1 在 overlap 0.62 下路由错配加剧
- 保留 v8_5 的 soft blend，不再动 eval routing

## 单点变更
- 配置：`router.prototype_update_steps: 4`（3→4 遍段内伪标签原型 EMA）

## 假设
v8_5 seg6 seen=0.455 但 oracle 仅 0.34 → 原型拟合仍不足；多 1 遍 EMA 在分支增多/overlap 升高时收紧原型，不增加 LoRA epoch、不改评测路由。

## 成功判据
- seg7 seen≥0.40；终局 seen≥0.36

## 运行
- tmux: `v8_sota_8` | 日志: `v8_sota_8.log` | seed=123
