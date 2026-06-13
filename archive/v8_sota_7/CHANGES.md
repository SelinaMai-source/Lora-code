# v8_sota_7 —— Eval Hard Routing (No Soft Blend)

日期：2026-06-12  
失败版本：v8_sota_6（seg15 早停，seen=0.264）  
基座：**v8_sota_5**（spawn-sync + prototype_update_steps=3，**无** segment_anchor_refresh）

## 失败结论（v8_sota_6）
- segment anchor refresh **回退**：seg15 seen=0.264，oracle 0.19
- 证伪段末 anchor 重同步策略

## 单点变更
- 配置：`router.soft_routing: false`（评测硬 top-1，取消 soft top-3 混合）

## 假设
v8_5 在 spawn-sync+3pass 下 seg6 seen=0.455 但 oracle 仅 0.34 → soft blend 可能虚高后崩盘；硬路由在强原型下更稳。

## 运行
- tmux: `v8_sota_7`
