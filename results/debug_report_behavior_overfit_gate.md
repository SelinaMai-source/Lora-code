# Baseline 行为门控调试报告（overfit-8 / teacher-forced 对齐）

**生成日期**：2026-03-22  
**范围**：仅基线（LoRA + 手动/模板监督），未引入 drift/router/replay/LoRA bank 等研究模块。

---

## 1. Teacher-forced 指标是否与 causal LM loss 对齐？

### 结论（Stage 1）

**原实现不正确。** 训练与评估中的「teacher-forced token accuracy」此前将 `argmax(logits[t])` 与 `labels[t]` 在同一时间步比较；而 HuggingFace `CausalLM` 在传入 `labels` 时，交叉熵使用的是 **移位后的监督位置**：

- `shift_logits = logits[:, :-1, :]`
- `shift_labels = labels[:, 1:]`
- 仅在 `shift_labels != -100` 的位置累计 loss / accuracy。

### 代码修复（已合入）

- 共享实现：`core/causal_lm_metrics.py` 中 `teacher_forced_token_accuracy_shifted(...)`。
- 训练：`HFCausalLMBackbone.fit_batch` 的 `train_answer_token_acc` 改为移位对齐；并返回 `num_loss_tokens`（与 accuracy 分母一致）。
- 评估：`core/evaluate.py` 中 `teacher_forced_answer_token_acc` 改为移位对齐；并附加 `teacher_forced_num_loss_tokens`、`teacher_forced_num_supervised_label_tokens`（后者为 `labels != -100` 计数，可与前者不同，属正常现象）。

### 断言与 JSON 转储

- **逐样本 JSON**（overfit-8）：`results/runs/<run_id>/debug/overfit8/teacher_forced_audit_initial.json`（训练前）、`teacher_forced_audit_final.json`（训练后）。  
  字段包含：`raw_input_ids`、`decoded_token_pieces`、`labels`、`supervised_mask`、`shifted_labels_for_loss`、`shifted_argmax_predictions`、`first/last_supervised_token_index`、金/预测监督片段解码等。
- **严格断言**：配置 `debug_tools.strict_teacher_metric_assertions: true` 时，在 dump 中校验 `num_loss_tokens == count(shifted_labels != -100)`；首监督 token 与 target 的启发式一致性默认仅记录，严格模式下 `assert`（易因分词边界误报，默认关闭）。

### 本地烟测观测（3 step，`behavior_gate_smoke_shift_metric`）

修复后，`overfit8_steps.csv` 中 `num_loss_tokens` 与移位 accuracy 分母一致；`teacher_forced_shifted_token_acc_mean` 随 loss 下降而上升（与「可学习」一致）。  
注意：`train_answer_token_acc`（训练 `train` 模式，含 LoRA dropout）与 `teacher_forced_shifted_token_acc_mean`（`eval` 前向）会有小幅差异，**定义已对齐**，差异来自 dropout / 模式而非索引错误。

---

## 2. 手动 mask vs「官方式」completion-only 边界

### 实现说明（Stage 2）

未新增 `trl` 依赖。在 `core/train_labels.py` 中提供：

- `train_labeling_mode: manual`：沿用原逻辑，按 `format_for_infer(..., add_generation_prompt=True)` 的 token 长度 mask 前缀。
- `train_labeling_mode: completion_only`：在完整序列中查找 `completion_only_response_template`（默认 `<|start_header_id|>assistant<|end_header_id|>\n\n`）首次出现，从 **模板结束之后** 开始监督（HF/TRL completion-only 语义）。

### 结论

在 **Llama-3.1-8B-Instruct** 与当前 `apply_chat_template` 配置下，对随机短样例与 overfit 审计样本验证：`manual` 与 `completion_only` 得到的 **`labels` 完全一致**（`manual_prompt_len == completion_supervise_start`）。  
因此 **手动 mask 与模板边界在此设置下并非疑点**；若换模板/模型，应重新比对两模式下的 `labels` 与审计 JSON。

| 运行配置 | 说明 |
|----------|------|
| Path A | `configs/behavior_gate_manual_qv.yaml` |
| Path B | `configs/behavior_gate_completion_qv.yaml` |

完整对比请运行脚本后比较两次 run 的 `overfit8_steps.csv` 与 `teacher_forced_audit_*.json`。

---

## 3. LoRA `target_modules` 容量消融

在相同 `r=16, alpha=32, dropout=0.05`、仅更换 `target_modules` 时，可训练参数规模（本机一次加载统计）：

| 配置 | target_modules | trainable LoRA 参数 |
|------|----------------|---------------------|
| lora_qv | q_proj, v_proj | 6,815,744 |
| lora_qkvo | q, k, v, o | 13,631,488 |
| lora_all_linear | all-linear（PEFT 字符串） | 41,943,040 |

对应配置文件：

- `configs/behavior_gate_manual_qv.yaml`
- `configs/behavior_gate_manual_qkvo.yaml`
- `configs/behavior_gate_manual_alllinear.yaml`

**哪一个在 overfit-8 上最好**：需以完整 `overfit_steps`（默认 120）跑完后比较最后一次日志行的 `exact_match_count` 与 `prefix1_acc`（或 `overfit8_steps.csv` 末行）。容量更大通常更有利于极小集过拟合；若 qv 已能门控通过，可不再加大参数。

---

## 4. 确定性生成（debug / overfit）

`HFCausalLMBackbone.generate` / `generate_with_ids` 现使用 `transformers.GenerationConfig`：

- `do_sample=False`、`num_beams=1`
- 显式 `temperature=1.0`、`top_p=1.0`（避免部分版本对默认 generation_config 报无效采样字段警告）
- `pad_token_id` / `eos_token_id` 来自 tokenizer
- `use_cache=True`（推理路径）

可在 YAML 中覆盖：`model.gen_do_sample`、`model.gen_num_beams`。

---

## 5. 观测性汇总表（需在完整跑完后填写末行）

运行：

```bash
cd /root/autodl-tmp/Lora-code
bash scripts/run_behavior_overfit_gate.sh
```

对各 run 打开 `results/runs/<output.run_name>/debug/overfit8/overfit8_steps.csv`，取 **最后一行**（或 `grep` 最大 step）填入：

| 实验 | train_loss | teacher_forced_shifted_token_acc_mean | exact_match | token_f1_mean | lcs_overlap_mean | prefix1 | prefix3 | prefix5 |
|------|------------|--------------------------------------|-------------|---------------|------------------|---------|---------|---------|
| manual_qv |  |  |  |  |  |  |  |  |
| completion_qv |  |  |  |  |  |  |  |  |
| manual_qkvo |  |  |  |  |  |  |  |  |
| manual_alllinear |  |  |  |  |  |  |  |  |

**烟测示例（仅 3 step，manual_qv，不代表门控已通过）**：末行 `train_loss≈2.335`，`teacher_forced_shifted_token_acc_mean≈0.548`，`exact_match=0/8`，`prefix1_acc=0`。

---

## 6. 推荐的基线配置（诊断可信优先）

1. **指标**：使用修复后的移位 `train_answer_token_acc` / `teacher_forced_answer_token_acc` 与 `num_loss_tokens`。  
2. **监督边界**：Llama 3.1 + 当前模板下 **manual 与 completion_only 等价**；保留 completion_only 作跨模型回归检查。  
3. **容量**：若 qv 长期无法过拟合 8 条，优先尝试 **qkvo** 或 **all-linear**（见上表参数规模）。  
4. **解码**：保持 greedy + 固定 eos/pad；`overfit_gen_max_new_tokens` 足够覆盖参考答案。  
5. **门控**：以 `exact_match ≥ 6/8` 且 `prefix1_acc ≥ 0.75` 为通过条件时，应以 **完整步数** 的 `overfit8_steps.csv` 与 `step_XXXX_predictions.json` 为准。

---

## 7. 变更文件清单（最小化、已注释/文档化）

- `core/causal_lm_metrics.py`（新建）
- `core/train_labels.py`（新建）
- `core/debug_teacher_audit.py`（新建）
- `core/models/base_model.py`（移位 accuracy、GenerationConfig、label 构建接入、`num_loss_tokens`）
- `core/evaluate.py`（teacher-forced 移位对齐、额外计数字段）
- `core/train.py`（overfit 审计 JSON、CSV 扩展列、teacher-forced mean）
- `core/models/lora_wrapper.py`（`target_modules` 支持 `"all-linear"` 字符串）
- `configs/behavior_gate_*.yaml`、`scripts/run_behavior_overfit_gate.sh`

---

## 8. 真实瓶颈（简明）

1. **主要诊断噪声来源**：原 teacher-forced / batch token accuracy 与 **HF causal LM loss 的移位监督不一致**，导致「loss 很低但 acc≈0」的假象；修复后 acc 与 loss 在定义上可对照。  
2. **剩余瓶颈（修复指标后）**：在相同解码与模板下，若 teacher-forced 已上升而 **exact_match 仍低**，则问题在 **自由生成与 teacher forcing 的分布差**（容量、步数、学习率、或任务本身对 greedy 解码敏感），而非监督 mask 与 loss 索引不一致。烟测中 3 step 内 teacher-forced 已明显上升但 EM 仍为 0，符合「尚需更多步数或更大 LoRA 容量」的预期。
