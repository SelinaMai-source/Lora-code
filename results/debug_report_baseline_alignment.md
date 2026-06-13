# Debug Report: Baseline Format Alignment (CITB + Llama-3.1-8B + PEFT LoRA)

## What Was Wrong Before

- Training/inference/eval prompt formatting was inconsistent (manual string concatenation with `指令/输入/输出`).
- Training loss could decrease while generation EM stayed at 0 because:
  - train supervision boundary and inference prompt family were not strictly unified under chat template;
  - generation extraction/normalization had legacy assumptions tied to ad-hoc markers;
  - overfit behavior often produced long continuations and format drift.

## What Code Paths Were Changed

- Added shared chat-template utility:
  - `core/formatting.py`
  - `build_chat_messages(...)`
  - `format_for_train(...)`
  - `format_for_infer(...)`
- Updated baseline training path to use `(instruction, input_text)` tuples and let backbone format with chat template:
  - `core/models/base_model.py`
  - `baselines/sequential_lora/method.py`
  - `baselines/replay_lora/method.py`
  - `baselines/periodic_multilora/method.py`
  - `baselines/router_only/method.py`
  - `core/train.py` (overfit/train helper/router helper prompt flow)
- Updated eval path to use chat template prompts and continuation-only comparison diagnostics:
  - `core/evaluate.py`
  - Added per-example `token_f1`, `lcs_overlap`, `bad_prefix_mismatch`, `formatted_infer_prompt`
  - Added aggregate `token_f1_mean`, `lcs_overlap_mean`

## Whether Train and Infer Now Use the Same Chat Template Family

Yes.

- Train prompt and full text are generated from `tokenizer.apply_chat_template(...)`.
- Infer prompt is generated from the same helper with `add_generation_prompt=True`.
- Saved examples confirm same family (`<|begin_of_text|> ... <|start_header_id|>user ... <|start_header_id|>assistant`).

## Whether Supervised Tokens Align with Assistant Answer Span

Yes, after refactor.

- Prompt prefix tokens are masked to `-100`.
- Supervised tokens map to assistant answer tokens + assistant stop token.
- Guard rails:
  - runtime check `num_supervised_tokens > 0`
  - alignment dump includes decoded supervised span for direct audit.

## Experiment 1: Overfit-8 Debug Run

- Config: `configs/baseline_alignment_overfit.yaml`
- Run dir: `results/runs/baseline_alignment_overfit/`
- `overfit8_steps.csv`:
  - step1 loss: `4.4926`
  - step10 loss: `0.2629`
  - step20 loss: `0.000793`
- Overfit generation exact-match (same 8 samples, greedy decode):
  - step1: `0/8`
  - step5: `1/8`
  - step10: `2/8`
  - step20: `2/8`

Interpretation:
- Alignment fixes improved behavior from previous all-zero overfit EM to non-zero (`2/8`).
- Still not full behavioral overfit at sequence EM level.

## Experiment 2: Single-Segment Baseline Run

- Config: `configs/baseline_alignment_single_segment.yaml`
- Run dir: `results/runs/baseline_alignment_single_segment/`
- Final metrics (`final_metrics.json`):
  - `train.train.loss = 3.4753`
  - `train.train.answer_token_acc = 0.0125`
  - `train.grad_norm = 7.9630`
  - `eval.current_score = 0.0`
  - `eval.token_f1_mean = 0.0782`
  - `eval.lcs_overlap_mean = 0.1635`
- Eval diagnostics (`eval_debug/eval_segment_000.json`):
  - `num_bad_prefix_mismatch = 8/8`

Interpretation:
- Strict EM is still zero on eval split.
- Prefix-level mismatch is systematic, indicating model behavior mismatch (not mainly normalization truncation).

## Formatted Training Examples (2)

From `results/runs/baseline_alignment_single_segment/debug/alignment/train_alignment_examples.json`:

1) Train prompt (excerpt):
- `<|begin_of_text|><|start_header_id|>system...<|start_header_id|>user...Input: [...]<|eot_id|><|start_header_id|>assistant...`
- Target: `I just hope you're not planning a Juggernaut ~~ then it'd be almost irresponsible of me to not do anything ya?`
- Decoded supervised span: `I just hope ... ya?<|eot_id|>`

2) Train prompt (excerpt):
- Same template family and assistant continuation boundary.
- `labels != -100` exactly corresponds to assistant answer span.

## Formatted Inference Prompts (2)

From `results/runs/baseline_alignment_single_segment/eval_debug/eval_segment_000.json`:

1) Example idx0 `formatted_infer_prompt`:
- `<|begin_of_text|> ... <|start_header_id|>user ... Input: [...] <|eot_id|><|start_header_id|>assistant ...`

2) Example idx7 `formatted_infer_prompt`:
- Same structure and generation start boundary.

## Gold vs Prediction Examples (3)

1) Single-segment eval idx0:
- Gold: `yeah, honestly, ...`
- Pred: `do either. I think I can do that ...` (off-topic continuation)
- EM: false, token_f1: ~0.064

2) Single-segment eval idx1:
- Gold: `okay. fair enough. one reason it might matter is...`
- Pred: `i am not sure if you are looking to do anything with me...` (repetitive drift)
- EM: false, token_f1: ~0.138

3) Overfit step20 idx1:
- Gold: `Fair enough. I was going to send the video in chat...`
- Pred: `I was going to send the video in a text...`
- Near-semantic match but strict EM false.

## Is Main Problem Now (a/b/c/d/e)?

- (a) Template mismatch: **mostly fixed**
- (b) Prediction extraction bug: **fixed to continuation-based extraction**
- (c) Label-mask misalignment: **fixed with assistant-span masking + assertions**
- (d) Metric too strict: **partially true** (near matches still fail EM)
- (e) Model still not behaviorally overfitting: **still true (primary remaining issue)**

## Top 3 Remaining Root-Cause Hypotheses

1) **Behavioral underfitting at sequence level** despite low loss:
   token-level objective improves but full-sequence exact output control is weak.
2) **Small-step overfit setup still not enough for strict generation matching**:
   generated responses drift into verbose continuations instead of concise targets.
3) **CITB dialogue target style diversity + strict EM**:
   many acceptable semantically-close generations fail exact string match.

## Bottom Line

- Baseline validity plumbing is now aligned and auditable:
  - unified chat templates across train/infer/eval,
  - assistant-span supervision verified,
  - continuation-only prediction extraction.
- Overfit-8 exact-match improved from all-zero behavior to non-zero (`2/8`), but single-segment strict EM remains `0.0`.
