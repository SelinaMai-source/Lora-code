# Overfit-8：序列行为诊断（非调参、非研究模块）

## 目标现象（当前假设）

在 **baseline LoRA + 统一 chat 模板** 下，反复出现：

| 信号 | 典型表现 |
|------|-----------|
| Train loss | → 近 0 |
| Shifted teacher-forced token acc | → ~1.0 |
| Train-mode answer token acc | → ~1.0 |
| Greedy exact match（`evaluate._normalize`） | 仍低（如 ~1/8） |
| Prefix-1/3/5 | 偏低 |

**工作假设**：teacher-forced / 训练前向路径上的条件分布已拟合；**开环自回归生成**（同权重、同 infer prompt、greedy）与参考文本在 **轨迹层面** 不对齐。  
本文档**不**把根因默认归为 mask/shift 实现错误；那些应已通过独立审计与移位指标修复处理。

**不做**：drift、LoRA bank、router、overlap loss；泛泛学习率/步数网格搜索（除非诊断结论明确要求）。

---

## Step 2.5 — 诊断定义审计（进入 Step 3 前建议执行）

不跑新训练，只读已有 `debug/overfit8` 产物，检查 rank 约定、`gold_equals_greedy` 与 rank 一致性、打印 step20 失败表、汇总 margin CSV：

```bash
python core/sequence_diag_audit.py results/runs/<run_id>/debug/overfit8
```

生成：

- `STEP25_DIAGNOSIS_AUDIT.md`（说明 + 表 + 位置对齐）
- `first_token_margin_aggregate_by_step.csv`（按 step 汇总 `count_gold_rank_le_1` 等）

## 分阶段执行（推荐顺序）

| 阶段 | YAML 开关 | 产物 |
|------|-----------|------|
| **1** | `enable_sequence_behavior_diagnosis: true`，`run_failure_decomposition: true`，`run_first_token_audit: true`，其余 `false` | failure JSON/CSV + first_token JSON + `first_token_margin_over_time.csv` |
| **2** | 在 1 基础上 `run_prefix_rollout: true` | `step_*_prefix_rollout.json`、`prefix_rollout_summary.csv` |
| **3** | `run_decode_ablation: true` | `decode_ablation.json`、`.csv` |
| **4** | `run_overfit_ladder: true` | `overfit_ladder.csv` |

主开关：`enable_sequence_behavior_diagnosis`。`run_failure_decomposition` / `run_first_token_audit` 在总开关为 true 时默认 true，可按需关掉其一。

## 诊断管线（代码入口）

1. 配置：`debug_tools.enable_sequence_behavior_diagnosis: true`（见 `configs/baseline_alignment_overfit.yaml`）。
2. 训练入口：`python core/train.py --config configs/baseline_alignment_overfit.yaml` → `_run_overfit_8_mode`（`core/train.py`）。
3. 实现模块：`core/sequence_behavior_diag.py`（Part A）、`core/overfit_sequence_diagnostics.py`（Part B–F）、`core/models/base_model.py`（`num_beams`、`generate_with_forced_answer_prefix`）。

### 输出文件清单（`results/runs/<run_id>/debug/overfit8/`）

| 文件 | Part |
|------|------|
| `step_XXXX_failure_analysis.json`, `step_XXXX_failure_summary.csv` | A |
| `step_XXXX_first_token_audit.json`, `first_token_margin_over_time.csv` | B |
| `step_XXXX_prefix_rollout.json`, `prefix_rollout_summary.csv` | C |
| `decode_ablation.json`, `decode_ablation.csv` | D |
| `overfit_ladder.csv` | E |
| `results/debug_report_sequence_behavior_diagnosis.md` | F（运行结束时写入 `results/` 根目录） |

### 每 eval 步产物（`results/runs/<run_id>/debug/overfit8/`）

| 文件 | 回答的问题 |
|------|------------|
| `step_XXXX_failure_analysis.json` + `step_XXXX_failure_summary.csv` | 失败主要是首 token、前缀漂移、表面形式、停词/过长、还是内容错？ |
| `step_XXXX_first_token_audit.json` + 追加 `first_token_margin_over_time.csv` | 第一个 gold 答案 token 在 greedy 下排名、概率、logit 差；是否「差一点选对」？ |
| `step_XXXX_prefix_rollout.json` + 追加 `prefix_rollout_summary.csv` | 强喂 0/1/3/5 个 gold token（若 gold 更短则 **钳位到全长**，避免空预测污染指标）后再生成，EM/prefix 是否陡升？CSV 含 `n_clamped_short_gold`。 |

### 训练结束后（可选/可配置）

| 文件 | 回答的问题 |
|------|------------|
| `decode_ablation.json` / `decode_ablation.csv`（`run_decode_ablation: true`） | beam 相对 greedy 是否显著更好？（质量是否在分布里但路径脆） |
| `overfit_ladder.csv`（`run_overfit_ladder: true`，**默认关闭**，四次从 `ladder_init` 冷启动） | 失败从 n=1/2/4/8 哪一档开始恶化？ |

### 总览报告（每次跑完覆盖写入）

- `results/debug_report_sequence_behavior_diagnosis.md`：由 `write_sequence_behavior_report` 聚合 CSV/JSON，并给出启发式「主瓶颈」标签。

---

## 如何读结果（与现象的对应关系）

- **first_token_audit**：gold 常排第 2 名且概率接近 greedy → 多为 **解码路径 / 首步 margin**；排名很差 → 首步行为未与开环对齐。
- **prefix_rollout 0→1**：EM 大幅上升 → 不稳定集中在 **前几步**；强喂到 5 仍差 → **深序列** 或 **停词/格式** 仍占主因。
- **failure_summary**：`whitespace_or_newline` / `punctuation_only` 高 → **表面形式**；`wrong_stop_or_overgenerate` 高 → **生成长度/停止**；`content_wrong` 为主且 TF 仍 1.0 → **开环轨迹与 teacher 条件不一致**（非「没学到 token」）。
- **decode_ablation**：beam 明显优于 greedy → 参考序列可能在 **联合概率** 下尚可，greedy **局部最优**；beam 也无增益 → **分布质量** 不足或 eval 与训练解码条件仍不一致（需对照 `GenerationConfig`）。

---

## 与 proposal 主线的关系

主 proposal 中的 continual + drift + bank + router + overlap **在此阶段刻意不推进**，直到 overfit-8 上的 **开环行为** 可被上述 artifact **解释或定位**。通过行为门控后再恢复主实验比较才有意义。
