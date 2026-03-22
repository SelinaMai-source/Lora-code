"""
Build `input_ids` / `labels` for supervised causal LM training.

Supports:
  - manual: mask prompt tokens using `format_for_infer(..., add_generation_prompt=True)` length
  - completion_only: mask through the first occurrence of `response_template` (HF/TRL-style boundary)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple

from core.formatting import format_for_infer, format_for_train


@dataclass
class SupervisedEncoding:
    full_ids: List[int]
    labels: List[int]
    manual_prompt_len: int
    """Index of first supervised token under manual masking (= number of leading masked tokens)."""
    completion_supervise_start: int
    """First supervised index when using completion_only template search (same as manual when aligned)."""
    prompt_text: str
    full_text: str


def _find_subsequence(haystack: List[int], needle: List[int]) -> int:
    if not needle or len(needle) > len(haystack):
        return -1
    n = len(needle)
    for i in range(len(haystack) - n + 1):
        if haystack[i : i + n] == needle:
            return i
    return -1


def build_supervised_labels(
    tokenizer: Any,
    instruction: str,
    input_text: str,
    target: str,
    *,
    max_len: int,
    min_target_tokens: int,
    mask_eos_token_in_labels: bool,
    mask_all_special_tokens_in_labels: bool,
    labeling_mode: str,
    completion_only_response_template: str,
) -> SupervisedEncoding:
    prompt_text = format_for_infer(tokenizer, instruction, input_text, add_generation_prompt=True)
    full_text = format_for_train(tokenizer, instruction, input_text, str(target))["full_text"]

    prompt_ids = tokenizer(prompt_text, add_special_tokens=False, truncation=False)["input_ids"]
    full_ids_raw = tokenizer(full_text, add_special_tokens=False, truncation=False)["input_ids"]

    manual_prompt_len = min(len(prompt_ids), len(full_ids_raw))

    needle = tokenizer(completion_only_response_template, add_special_tokens=False)["input_ids"]
    idx = _find_subsequence(full_ids_raw, needle)
    if idx < 0:
        completion_supervise_start = manual_prompt_len
    else:
        completion_supervise_start = idx + len(needle)

    labels_raw = list(full_ids_raw)
    if str(labeling_mode).lower() == "completion_only":
        mask_upto = completion_supervise_start
    else:
        mask_upto = manual_prompt_len

    for i in range(min(mask_upto, len(labels_raw))):
        labels_raw[i] = -100

    if bool(mask_eos_token_in_labels) and tokenizer.eos_token_id is not None:
        eos_id = int(tokenizer.eos_token_id)
        for i, tok_id in enumerate(full_ids_raw):
            if tok_id == eos_id:
                labels_raw[i] = -100

    if bool(mask_all_special_tokens_in_labels):
        special_ids = {int(x) for x in (tokenizer.all_special_ids or [])}
        if special_ids:
            for i in range(mask_upto, len(full_ids_raw)):
                if int(full_ids_raw[i]) in special_ids:
                    labels_raw[i] = -100

    min_tgt = max(1, int(min_target_tokens))
    if len(full_ids_raw) > max_len:
        dropped = len(full_ids_raw) - max_len
        full_ids = full_ids_raw[-max_len:]
        labels = labels_raw[-max_len:]
        if all(v == -100 for v in labels):
            keep = min(min_tgt, max_len)
            for i in range(max(0, max_len - keep), max_len):
                labels[i] = full_ids[i]
        manual_prompt_len = max(0, int(manual_prompt_len) - int(dropped))
        completion_supervise_start = max(0, int(completion_supervise_start) - int(dropped))
    else:
        full_ids = full_ids_raw
        labels = labels_raw

    return SupervisedEncoding(
        full_ids=list(full_ids),
        labels=list(labels),
        manual_prompt_len=int(manual_prompt_len),
        completion_supervise_start=int(completion_supervise_start),
        prompt_text=str(prompt_text),
        full_text=str(full_text),
    )


def first_supervised_index(labels: List[int]) -> int:
    for i, v in enumerate(labels):
        if v != -100:
            return i
    return len(labels)


def assert_first_supervised_matches_target_start(
    tokenizer: Any,
    labels: List[int],
    full_ids: List[int],
    target_text: str,
) -> Tuple[bool, str]:
    """
    Heuristic: decoded text of the first supervised token should appear in the raw target
    (assistant answer), or match the first whitespace-delimited token.
    """
    idx = first_supervised_index(labels)
    if idx >= len(full_ids):
        return False, "no supervised token"
    first_id = int(full_ids[idx])
    piece = tokenizer.decode([first_id], skip_special_tokens=False)
    tgt = (target_text or "").strip()
    if not tgt:
        return True, "empty target; skipped"
    if piece.strip() and piece.strip() in tgt:
        return True, "substring ok"
    first_word = tgt.split()[0] if tgt.split() else ""
    if first_word and (first_word in piece or piece.strip().startswith(first_word[: max(1, len(first_word) // 2)])):
        return True, "first word heuristic ok"
    return False, f"first_supervised_decoded={piece!r} vs target_head={tgt[:40]!r}"
