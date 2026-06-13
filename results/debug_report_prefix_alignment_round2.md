# Round-2 Prefix Alignment Debug Report

## 1) 本轮做了什么
- 目标：定位并修复 `bad_prefix_mismatch` 全为 true 的瓶颈，聚焦 assistant 起始边界、continuation slicing、行为过拟合。
- 代码改动（最小化）：
  - `core/formatting.py`：`format_for_infer(..., add_generation_prompt: bool=True)`，支持 A/B。
  - `core/models/base_model.py`：
    - 新增 `generate_with_ids()`，导出 `generated_full_ids / generated_continuation_ids / infer_prompt_token_ids` 并断言切片一致性。
    - 训练侧新增 token-level 审计写盘：`alignment_token_audit.json`（含 `prompt_token_len / supervised_start_idx / decoded_prompt_tail / decoded_supervised_head`）。
    - debug mask：默认不监督 `eos` 控制 token（debug-only）。
  - `core/evaluate.py`：
    - 新增 `prefix_1/3/5_match`（逐样本+聚合）。
    - 可选 teacher-forced 诊断：`teacher_forced_loss`、`teacher_forced_answer_token_acc`。
    - 保存 infer token 审计字段（prompt ids、continuation ids、decoded heads/tails）。
    - 聚合中新增 `likely_assistant_start_or_continuation_boundary` 标记。
  - `core/train.py` overfit-8：
    - 100 steps，greedy，每 10 步记录 `exact_match_count + prefix1/3/5`。
    - 输出 `overfit8_steps.csv`。
    - 新增 generation-prompt A/B 消融输出 `generation_prompt_ablation.csv`。

## 2) 实验与产物
- 实验1（overfit-8 round2）：
  - config: `configs/baseline_alignment_overfit_round2.yaml`
  - 产物目录：`results/runs/baseline_alignment_overfit_round2/debug/`
  - 关键文件：
    - `overfit8/overfit8_steps.csv`
    - `overfit8/step_0100_predictions.json`
    - `generation_prompt_ablation.csv`
    - `generation_prompt_ablation_cont_heads.json`
    - `alignment_token_audit.json`
- 实验2（single-segment round2 diag）：
  - config: `configs/baseline_alignment_single_segment_round2.yaml`
  - 关键文件：
    - `results/runs/baseline_alignment_single_segment_round2/final_metrics.json`
    - `results/runs/baseline_alignment_single_segment_round2/eval_debug/eval_segment_000.json`
    - `results/runs/baseline_alignment_single_segment_round2/debug/alignment_token_audit.json`

## 3) A项结论：训练侧 supervised span 起点是否对齐
- 结论：**大多数样本对齐正确，但存在边界污染样本（控制 token 混入）**。
- 证据（train token audit）：
  - 示例A（异常）：`Hahah yeah`
    - `decoded_supervised_head`: `Hahah yeah<|eot_id|>`
    - `span_prefix_match_with_gold=false`
    - `includes_control_tokens_unexpected=true`
    - 说明：虽然文本可见部分正确，但监督头部仍沾到控制符语义边界。
  - 示例B（正常）：`Fair enough...`
    - `span_prefix_match_with_gold=true`
    - `includes_control_tokens_unexpected=false`
    - `supervised_start_idx` 与 `prompt_token_len` 对齐。

## 4) B项结论：推理 continuation slicing 是否正确
- 结论：**切片逻辑本身正确，不是主要 bug**。
- 证据：
  - eval 每条都保存了 `generated_full_ids` 与 `generated_continuation_ids`，并通过断言：`generated_continuation_ids == generated_full_ids[prompt_len:]`（运行未触发断言）。
  - 每条预测均来自 continuation decode（`raw_generated_text` 与 continuation 对应）。
  - `eval_segment_000.json` 中 8/8 都有 `generated_continuation_ids`，无空 continuation。

## 5) C项结论：add_generation_prompt A/B
- 文件：`generation_prompt_ablation.csv`

| variant | exact_match_count | prefix1_acc | prefix3_acc | prefix5_acc |
|---|---:|---:|---:|---:|
| A_add_generation_prompt_true | 1 | 0.25 | 0.25 | 0.125 |
| B_add_generation_prompt_false | 0 | 0.0 | 0.0 | 0.0 |

- 额外证据（`generation_prompt_ablation_cont_heads.json`）：
  - B 变体多条 continuation 头部出现 `<|start_header_id|>assistant...`，即 assistant header 被“再生成”。
  - 这会直接破坏 prefix token 对齐并拉低 EM。
- 结论：**当前模板下 `add_generation_prompt=True` 明显更好，B 会恶化 assistant-start 对齐。**

## 6) D项结论：overfit-8 从 loss overfit 到 behavior overfit？
- 文件：`overfit8_steps.csv`
- 轨迹摘要：
  - step1: `loss=4.3478, EM=0/8, prefix1=0.0`
  - step10: `loss=0.0921, EM=0/8, prefix1=0.25`
  - step20: `loss=0.00229, EM=1/8, prefix1=0.25`
  - step100: `loss=0.000047, EM=1/8, prefix1=0.25, prefix3=0.25, prefix5=0.125`
- 结论：
  - **未达到行为过拟合成功线（>=6/8）**。
  - 虽然 loss 极低，但 prefix 指标长期停滞，说明不是纯优化稳定性问题，而是生成行为/起始模式未学到。

## 7) E项结论：teacher-forced vs free-generation
- 文件：`eval_segment_000.json`
- 结果：
  - free generation：`EM=0`，`prefix_1/3/5 全为 false (8/8)`。
  - teacher-forced：
    - `teacher_forced_loss` 约在 `2.28 ~ 3.50`（8条）
    - `teacher_forced_answer_token_acc` 为 `0.0`（8条）
- 解读：
  - **teacher-forced 也不强**（并非“老师强、自由生成弱”的典型 exposure bias 场景）。
  - 模型尚未把 gold continuation 的 token 分布学到足够可用水平。

## 8) 2条 infer token audit（节选）
- 示例1（single-segment eval idx0）：
  - `decoded_continuation_head`: 以 `"do either. what do you think..."` 起始
  - gold 起始：`"yeah, honestly, ..."`
  - `prefix_1/3/5 = false/false/false`
- 示例2（single-segment eval idx7）：
  - `decoded_continuation_head`: `"fine. i'd rather you have it than austria..."`
  - gold 起始：`"i just hope you're not planning..."`
  - `prefix_1/3/5 = false/false/false`

## 9) 3条 gold vs prediction（来自 step_0100）
- 样本A（命中）：
  - gold: `I just hope you're not planning a Juggernaut ~~ ...`
  - pred: 完全一致（EM=1）。
- 样本B（前缀偏移）：
  - gold: `Russia said the same to me`
  - pred: `same to me, i just hope you're not planning...`（语义相关但首词错位）。
- 样本C（长答偏题）：
  - gold: `Talk is cheap, and after Spring resolution ...`
  - pred: 转向 “play with integrity ...” 主题，首词即错。

## 10) 单段 round2 总结指标
- `eval.current_score = 0.0`
- `eval.token_f1_mean = 0.1411`
- `eval.lcs_overlap_mean = 0.2558`
- `eval.extra.prefix_1_match_mean = 0.0`
- `eval.extra.prefix_3_match_mean = 0.0`
- `eval.extra.prefix_5_match_mean = 0.0`
- `eval.extra.num_bad_prefix_mismatch = 8`
- `eval.extra.likely_assistant_start_or_continuation_boundary = true`

## 11) 最终根因判定（硬结论）
- 最终判定：**(e) multiple issues combined**，其中主因排序：
  1. **(c) insufficient behavioral overfit（主因）**：loss 近零但 EM/prefix 长期停滞，teacher-forced 也弱。
  2. **(a) assistant boundary mismatch（次因）**：部分样本监督头/生成头仍可见控制边界污染，B变体会再生成 assistant header。
  3. **(d) metric too strict（次要）**：部分输出语义相关但首 token 错误，EM 进一步放大失败。
- 明确排除：
  - **(b) continuation slicing bug 不是主因**（切片断言和 token 审计均通过）。

## 12) 下一步建议（单步、最小动作）
- 先做一个最小边界净化补丁并复跑 overfit-8：
  - 在训练 supervision 中彻底去除 assistant header/eot 控制 token（不仅 eos），确保 `decoded_supervised_head` 第一个可见 token 总是 gold 首 token；
  - 保持 `add_generation_prompt=True`；
  - 不改方法学（不引入 drift/bank/router/replay）。
- 验收门槛：
  - overfit-8: `EM >= 6/8` 且 `prefix1_acc >= 0.75`；
  - single-segment: `num_bad_prefix_mismatch` 明显下降（不再 8/8）。

