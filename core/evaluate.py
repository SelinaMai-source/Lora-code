from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.causal_lm_metrics import count_supervised_label_tokens, teacher_forced_token_accuracy_shifted
from core.data import Example, Segment
from core.formatting import format_for_infer, format_for_train
from core.train_labels import build_supervised_labels


@dataclass
class EvalResult:
    current_score: float
    seen_avg_score: float
    forgetting: float
    num_seen_segments: int
    token_f1_mean: float
    lcs_overlap_mean: float
    extra: Dict[str, Any]


def evaluate_stream(
    *,
    model: Any,
    segments_seen: List[Segment],
    max_new_tokens: int = 64,
    router: Optional[Any] = None,
    lora_bank: Optional[Any] = None,
    segment_id: int,
    normalization_cfg: Optional[Dict[str, Any]] = None,
    save_debug_examples_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified evaluation for continual instruction tuning.

    Returns a metrics dict that is stable across modes:
      - current_score: accuracy on current segment eval
      - seen_avg_score: average accuracy across all seen segments
      - forgetting: max(prev_best - current) over seen segments (simplified)
      - num_seen_segments

    Extension points:
      - drift metrics
      - routing metrics (branch usage entropy, decision confidence)
      - overlap metrics (activation similarity)
    """

    # Track per-segment accuracy over time
    per_seg_acc: List[Tuple[int, float]] = []
    routing_stats = {"num_routed": 0, "branch_counts": {}}

    all_examples_for_dump: List[Dict[str, Any]] = []
    all_token_f1: List[float] = []
    all_lcs_overlap: List[float] = []
    all_prefix1: List[int] = []
    all_prefix3: List[int] = []
    all_prefix5: List[int] = []
    num_bad_prefix = 0
    for seg in segments_seen:
        acc, seg_routing, seg_examples = _eval_segment(
            model=model,
            segment=seg,
            max_new_tokens=max_new_tokens,
            router=router,
            lora_bank=lora_bank,
            segment_id=segment_id,
            normalization_cfg=normalization_cfg or {},
        )
        per_seg_acc.append((seg.segment_id, acc))
        _merge_routing_stats(routing_stats, seg_routing)
        all_examples_for_dump.extend(seg_examples)
        all_token_f1.extend([float(x.get("token_f1", 0.0)) for x in seg_examples])
        all_lcs_overlap.extend([float(x.get("lcs_overlap", 0.0)) for x in seg_examples])
        num_bad_prefix += sum(1 for x in seg_examples if bool(x.get("bad_prefix_mismatch", False)))
        all_prefix1.extend([int(bool(x.get("prefix_1_match", False))) for x in seg_examples])
        all_prefix3.extend([int(bool(x.get("prefix_3_match", False))) for x in seg_examples])
        all_prefix5.extend([int(bool(x.get("prefix_5_match", False))) for x in seg_examples])

    # current segment is the last in segments_seen
    current_score = per_seg_acc[-1][1] if per_seg_acc else 0.0
    seen_avg_score = sum(a for _, a in per_seg_acc) / max(1, len(per_seg_acc))

    # forgetting proxy: difference between best seen accuracy and current accuracy, clipped >= 0
    best_seen = max(a for _, a in per_seg_acc) if per_seg_acc else 0.0
    forgetting = max(0.0, best_seen - current_score)

    extra = {
        "per_segment_accuracy": [{"segment_id": sid, "accuracy": acc} for sid, acc in per_seg_acc],
        "routing": routing_stats,
        "token_f1_mean": float(sum(all_token_f1) / max(1, len(all_token_f1))),
        "lcs_overlap_mean": float(sum(all_lcs_overlap) / max(1, len(all_lcs_overlap))),
        "prefix_1_match_mean": float(sum(all_prefix1) / max(1, len(all_prefix1))),
        "prefix_3_match_mean": float(sum(all_prefix3) / max(1, len(all_prefix3))),
        "prefix_5_match_mean": float(sum(all_prefix5) / max(1, len(all_prefix5))),
        "num_bad_prefix_mismatch": int(num_bad_prefix),
    }
    extra["likely_assistant_start_or_continuation_boundary"] = bool(
        extra["prefix_1_match_mean"] < 0.5 if (len(all_prefix1) > 0) else False
    )
    if save_debug_examples_dir:
        tok = getattr(model, "tokenizer", None)
        _save_debug_examples(
            save_dir=save_debug_examples_dir,
            segment_id=segment_id,
            examples=all_examples_for_dump[: max(5, min(50, len(all_examples_for_dump)))],
            normalization_cfg=normalization_cfg or {},
            generation_cfg={
                "max_new_tokens": max_new_tokens,
                "do_sample": False,
                "eos_token_id": getattr(tok, "eos_token_id", None),
                "pad_token_id": getattr(tok, "pad_token_id", None),
            },
        )
    return asdict(
        EvalResult(
            current_score=float(current_score),
            seen_avg_score=float(seen_avg_score),
            forgetting=float(forgetting),
            num_seen_segments=int(len(segments_seen)),
            token_f1_mean=float(sum(all_token_f1) / max(1, len(all_token_f1))),
            lcs_overlap_mean=float(sum(all_lcs_overlap) / max(1, len(all_lcs_overlap))),
            extra=extra,
        )
    )


def _eval_segment(
    *,
    model: Any,
    segment: Segment,
    max_new_tokens: int,
    router: Optional[Any],
    lora_bank: Optional[Any],
    segment_id: int,
    normalization_cfg: Dict[str, Any],
) -> Tuple[float, Dict[str, Any], List[Dict[str, Any]]]:
    correct = 0
    total = 0

    routing_stats = {"num_routed": 0, "branch_counts": {}}

    tok = getattr(model, "tokenizer", None)
    if tok is None:
        raise RuntimeError("Model has no tokenizer; cannot format chat prompts for evaluation.")
    eval_examples = list(segment.eval)
    enable_infer_token_audit = bool(normalization_cfg.get("enable_infer_token_audit", False))
    enable_teacher_forced_eval = bool(normalization_cfg.get("enable_teacher_forced_eval", False))
    infer_token_audit_max_examples = int(normalization_cfg.get("infer_token_audit_max_examples", 8))
    teacher_forced_eval_max_examples = int(normalization_cfg.get("teacher_forced_eval_max_examples", 8))

    prompts = [format_for_infer(tok, ex.instruction, ex.input, add_generation_prompt=True) for ex in eval_examples]
    targets = [ex.output for ex in eval_examples]

    # If router/bank available, route per prompt (simplified hard routing).
    audited = enable_infer_token_audit and router is None and lora_bank is None and hasattr(model, "generate_with_ids")

    if router is not None and lora_bank is not None:
        branch_names = lora_bank.list_branches()
        branch_meta = lora_bank.state_dict()
        preds: List[str] = []
        for p in prompts:
            decision = router.predict_branch(
                prompt=p, branch_names=branch_names, branch_meta=branch_meta, segment_id=segment_id
            )
            routing_stats["num_routed"] += 1
            routing_stats["branch_counts"][decision.branch_name] = (
                routing_stats["branch_counts"].get(decision.branch_name, 0) + 1
            )
            # Switch adapter before generating (needed for real multi-adapter evaluation).
            if hasattr(lora_bank, "set_active_adapter"):
                lora_bank.set_active_adapter(decision.branch_name)
            preds.extend(model.generate([p], max_new_tokens=max_new_tokens))
    else:
        if audited:
            gen_audit = model.generate_with_ids(prompts, max_new_tokens=max_new_tokens)
            preds = [x.get("raw_generated_text", "") for x in gen_audit]
        else:
            gen_audit = None
            preds = model.generate(prompts, max_new_tokens=max_new_tokens)

    details: List[Dict[str, Any]] = []
    for ex, p, pred, y in zip(eval_examples, prompts, preds, targets):
        total += 1
        norm_pred = _normalize(pred, prompt=p, cfg=normalization_cfg)
        norm_gold = _normalize(y, prompt=p, cfg=normalization_cfg)
        matched = norm_pred == norm_gold
        token_f1 = _token_f1(norm_pred, norm_gold)
        lcs_overlap = _lcs_overlap(norm_pred, norm_gold)
        bad_prefix = _starts_incorrectly(norm_pred, norm_gold)

        pred_tokens = [t for t in norm_pred.split() if t]
        gold_tokens = [t for t in norm_gold.split() if t]
        prefix_1_match = pred_tokens[:1] == gold_tokens[:1]
        prefix_3_match = pred_tokens[:3] == gold_tokens[:3]
        prefix_5_match = pred_tokens[:5] == gold_tokens[:5]

        teacher_forced_loss: Optional[float] = None
        teacher_forced_answer_token_acc: Optional[float] = None
        teacher_forced_num_loss_tokens: Optional[int] = None
        teacher_forced_num_supervised_label_tokens: Optional[int] = None
        if enable_teacher_forced_eval and total <= teacher_forced_eval_max_examples:
            # Teacher-forced forward pass over (prompt + gold assistant target).
            # Token accuracy must use the same shifted span as HF causal LM loss
            # (argmax(logits[:, :-1]) vs labels[:, 1:], ignoring -100); same-index
            # argmax vs labels was incorrect and inflated mismatch diagnostics.
            import torch

            was_training = getattr(model, "model", None).training if getattr(model, "model", None) is not None else False
            # Keep it in eval for determinism.
            if getattr(model, "model", None) is not None:
                model.model.eval()

            with torch.no_grad():
                backbone_cfg = getattr(model, "cfg", None)
                max_len = int(getattr(backbone_cfg, "max_seq_len", 2048))
                min_tgt = int(getattr(backbone_cfg, "min_target_tokens_for_loss", 1))
                labeling_mode = str(
                    normalization_cfg.get("teacher_forced_labeling_mode")
                    or (getattr(backbone_cfg, "train_labeling_mode", None) if backbone_cfg is not None else None)
                    or "manual"
                )
                completion_template = str(
                    normalization_cfg.get("completion_only_response_template")
                    or (
                        getattr(backbone_cfg, "completion_only_response_template", None)
                        if backbone_cfg is not None
                        else None
                    )
                    or "<|start_header_id|>assistant<|end_header_id|>\n\n"
                )
                mask_eos = bool(normalization_cfg.get("mask_eos_token_in_labels", True))
                mask_spec = bool(normalization_cfg.get("mask_all_special_tokens_in_labels", True))

                enc = build_supervised_labels(
                    tok,
                    ex.instruction,
                    ex.input,
                    str(y),
                    max_len=max_len,
                    min_target_tokens=min_tgt,
                    mask_eos_token_in_labels=mask_eos,
                    mask_all_special_tokens_in_labels=mask_spec,
                    labeling_mode=labeling_mode,
                    completion_only_response_template=completion_template,
                )
                full_ids = enc.full_ids
                labels = enc.labels

                input_ids_t = torch.tensor([full_ids], dtype=torch.long, device=model.device)
                attention_mask_t = torch.ones_like(input_ids_t, dtype=torch.long)
                labels_t = torch.tensor([labels], dtype=torch.long, device=model.device)

                outputs = model.model(
                    input_ids=input_ids_t, attention_mask=attention_mask_t, labels=labels_t, return_dict=True
                )
                teacher_forced_loss = float(outputs.loss.detach().float().item())

                logits = outputs.logits  # [1, T, V]
                teacher_forced_answer_token_acc, _, n_loss = teacher_forced_token_accuracy_shifted(logits, labels_t)
                teacher_forced_num_loss_tokens = int(n_loss)
                teacher_forced_num_supervised_label_tokens = int(count_supervised_label_tokens(labels_t))

            if getattr(model, "model", None) is not None and was_training:
                model.model.train()

        if matched:
            correct += 1
        details.append(
            {
                "instruction": ex.instruction,
                "input_text": ex.input,
                "gold_output": y,
                "raw_generated_output": pred,
                "normalized_prediction": norm_pred,
                "normalized_gold": norm_gold,
                "match": matched,
                "token_f1": float(token_f1),
                "lcs_overlap": float(lcs_overlap),
                "bad_prefix_mismatch": bool(bad_prefix),
                "prefix_1_match": bool(prefix_1_match),
                "prefix_3_match": bool(prefix_3_match),
                "prefix_5_match": bool(prefix_5_match),
                "formatted_infer_prompt": p,
                "teacher_forced_loss": teacher_forced_loss,
                "teacher_forced_answer_token_acc": teacher_forced_answer_token_acc,
                "teacher_forced_num_loss_tokens": teacher_forced_num_loss_tokens,
                "teacher_forced_num_supervised_label_tokens": teacher_forced_num_supervised_label_tokens,
            }
        )

        # Optional continuation boundary / slicing audit.
        if audited and len(details) <= infer_token_audit_max_examples:
            idx = len(details) - 1
            audit = gen_audit[idx]
            prompt_len = int(audit.get("infer_prompt_token_len", 0))
            gen_full_ids = audit.get("generated_full_ids", [])
            gen_cont_ids = audit.get("generated_continuation_ids", [])
            assert gen_cont_ids == gen_full_ids[prompt_len:], "Eval slice assertion failed"

            # Verify decoded prediction comes from continuation ids only.
            tok_redecoded = tok.decode(gen_cont_ids, skip_special_tokens=True) if gen_cont_ids else ""
            if tok_redecoded != (audit.get("raw_generated_text", "") or ""):
                # Don't hard-fail; just record for debugging.
                details[-1]["continuation_decoding_mismatch"] = True

            details[-1].update(
                {
                    "formatted_infer_prompt_text": p,
                    "infer_prompt_token_ids": audit.get("infer_prompt_token_ids", []),
                    "infer_prompt_token_len": prompt_len,
                    "generated_full_ids": gen_full_ids,
                    "generated_continuation_ids": gen_cont_ids,
                    "decoded_prompt_tail": audit.get("decoded_prompt_tail", ""),
                    "decoded_continuation_head": audit.get("decoded_continuation_head", ""),
                    "raw_generated_text": audit.get("raw_generated_text", ""),
                }
            )

    acc = correct / max(1, total)
    return float(acc), routing_stats, details


def _merge_routing_stats(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
    dst["num_routed"] += int(src.get("num_routed", 0))
    for k, v in src.get("branch_counts", {}).items():
        dst["branch_counts"][k] = dst["branch_counts"].get(k, 0) + int(v)


def _normalize(s: str, *, prompt: str, cfg: Dict[str, Any]) -> str:
    text = str(s or "")
    if bool(cfg.get("keep_text_after_output_marker", True)):
        marker = "输出："
        if marker in text:
            text = text.split(marker)[-1]
    # Optional truncation for strict EM debugging.
    # Apply truncation consistently to prediction and gold.
    if bool(cfg.get("truncate_at_first_blankline", False)):
        text = text.split("\n\n", 1)[0]
    elif bool(cfg.get("truncate_at_first_newline", False)):
        text = text.split("\n", 1)[0]
    if bool(cfg.get("truncate_at_first_sentence_end", False)):
        import re
        m = re.search(r"[.!?]", text)
        if m is not None:
            text = text[: m.end()]
    if bool(cfg.get("remove_prompt_prefix", False)) and prompt and text.startswith(prompt):
        text = text[len(prompt) :]
    if bool(cfg.get("remove_special_tokens", True)):
        for tok in ["<s>", "</s>", "<pad>", "<unk>", "[PAD]", "[EOS]", "[BOS]"]:
            text = text.replace(tok, "")
    if bool(cfg.get("strip_whitespace", True)):
        text = text.strip()
    if bool(cfg.get("lowercase", True)):
        text = text.lower()
    return text


def _token_f1(pred: str, gold: str) -> float:
    p = [t for t in pred.split() if t]
    g = [t for t in gold.split() if t]
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    g_counts: Dict[str, int] = {}
    for t in g:
        g_counts[t] = g_counts.get(t, 0) + 1
    tp = 0
    for t in p:
        c = g_counts.get(t, 0)
        if c > 0:
            tp += 1
            g_counts[t] = c - 1
    prec = tp / max(1, len(p))
    rec = tp / max(1, len(g))
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def _lcs_overlap(pred: str, gold: str) -> float:
    a = pred.split()
    b = gold.split()
    if not a or not b:
        return 0.0
    n, m = len(a), len(b)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev = 0
        for j in range(1, m + 1):
            cur = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = cur
    lcs = dp[m]
    return float(lcs / max(1, len(b)))


def _starts_incorrectly(pred: str, gold: str) -> bool:
    p = [t for t in pred.split() if t]
    g = [t for t in gold.split() if t]
    if not p or not g:
        return False
    k = min(3, len(p), len(g))
    return p[:k] != g[:k]


def _extract_instruction_from_prompt(prompt: str) -> str:
    # Legacy helper: preserved for compatibility with old debug files.
    marker = "指令："
    if marker in prompt:
        rest = prompt.split(marker, 1)[1]
        return rest.split("\n", 1)[0]
    return prompt


def _save_debug_examples(
    *,
    save_dir: str,
    segment_id: int,
    examples: List[Dict[str, Any]],
    normalization_cfg: Dict[str, Any],
    generation_cfg: Dict[str, Any],
) -> None:
    d = Path(save_dir)
    d.mkdir(parents=True, exist_ok=True)
    out = {
        "segment_id": segment_id,
        "normalization_cfg": normalization_cfg,
        "generation_cfg": generation_cfg,
        "examples": examples,
    }
    (d / f"eval_segment_{segment_id:03d}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

