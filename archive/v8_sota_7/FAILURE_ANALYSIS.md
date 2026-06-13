---
failed_version: v8_sota_6
next_version: v8_sota_7
status: ready
agent_signoff: true
---
# 失败分析：v8_sota_6 → v8_sota_7

## 1. v8_sota_6 结果
- seg15 早停：seen=**0.264**，oracle=0.19
- 远差于冠军 v8_sota_5（0.353@seg18）

## 2. 证伪
segment_anchor_prototype_refresh（β=0.25）破坏原型稳定性，不应延续。

## 3. 下一版
**基座**：v8_sota_5  
**唯一变更**：`soft_routing: false`  
**判据**：seg7 seen≥0.40，终局 seen≥0.36
