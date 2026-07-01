# lora_run_v10 Strict Alignment — 状态

Updated: 2026-06-23 19:49:56 UTC

## Strict 矩阵

- **strict_cells**: 0
- **near_strict**: 0
- **blocked / needs audit**: 0

## CITB InstrDialog（Sequential / Replay LoRA）

- supervisor phase: `—`
- detail: —
- FT_INSTR AR (local): —
- Replay AR (local): —
- paper targets: FT 35.7 / Replay 40.4 (rougeL AR)

## 运行中

- CITB/GPU 进程数: 0
- 相关 tmux: —

## 长期目标

1. CITB paper 数值对齐（Stage-1 → Stage-2 → collect → 对比 → rerun）
2. 其余 baseline gap-repair（GPU 空闲时 CPU 并行）
3. LFPT5 clean rerun 排队
