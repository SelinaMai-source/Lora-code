# Evaluation Protocol

This protocol defines how continual instruction-tuning runs should be evaluated and reported.

## Metric Roles

- `strict_em`: exact match after the existing normalization. This is the strict lower-bound metric and must not silently truncate generations.
- `task_aware_score`: the primary candidate metric for short structured answers. It uses task-specific extraction before comparison.
- `token_f1_mean`: soft token overlap. It is useful when exact string form is too strict.
- `lcs_overlap_mean`: soft sequence overlap against the gold answer.
- `prefix_1/3/5_match_mean`: generation stability diagnostics, especially for first-token and open-loop failures.
- `teacher_forced_answer_token_acc`: training/diagnostic only. It must not be presented as open-loop generation accuracy.

## Task-Aware Scoring

Short structured tasks should be scored by extracting the answer-bearing field:

- `After step n`: extract the first `n` from `After step n` and compare the integer.
- Classification or short-label tasks: extract the first numeric, yes/no, true/false, A-D, or short label answer.
- Open-ended generation tasks: keep `strict_em` for reference, but use `token_f1_mean` and `lcs_overlap_mean` to explain partial correctness.

Every eval example must preserve:

- `raw_generated_output`: unmodified generation.
- `prediction_for_scoring`: the scoring view after first-line/first-sentence/regex extraction.
- `strict_match`: full-string exact match result.
- `task_aware_match`: task-aware result.
- `source_segment_id`, `source_segment_name`, `source_example_idx`: where the example came from.

## Generation Boundary Rules

- Strict EM uses the full normalized prediction.
- Task-aware score may use first-line, first-sentence, or regex extraction.
- Short answers may use a shorter `effective_max_new_tokens` during evaluation.
- Continuation slicing must remain prompt-only: decoded output should come from generated continuation ids, not from the formatted prompt.

## Reporting

Paper tables should report strict EM and task-aware score side by side. A method should not be judged from strict EM alone when task-aware score, token F1, or LCS show a different failure mode.
