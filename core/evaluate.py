from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from core.data import Example, Segment


@dataclass
class EvalResult:
    current_score: float
    seen_avg_score: float
    forgetting: float
    num_seen_segments: int
    extra: Dict[str, Any]


def evaluate_stream(
    *,
    model: Any,
    segments_seen: List[Segment],
    max_new_tokens: int = 64,
    router: Optional[Any] = None,
    lora_bank: Optional[Any] = None,
    segment_id: int,
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

    for seg in segments_seen:
        acc, seg_routing = _eval_segment(
            model=model,
            segment=seg,
            max_new_tokens=max_new_tokens,
            router=router,
            lora_bank=lora_bank,
            segment_id=segment_id,
        )
        per_seg_acc.append((seg.segment_id, acc))
        _merge_routing_stats(routing_stats, seg_routing)

    # current segment is the last in segments_seen
    current_score = per_seg_acc[-1][1] if per_seg_acc else 0.0
    seen_avg_score = sum(a for _, a in per_seg_acc) / max(1, len(per_seg_acc))

    # forgetting proxy: difference between best seen accuracy and current accuracy, clipped >= 0
    best_seen = max(a for _, a in per_seg_acc) if per_seg_acc else 0.0
    forgetting = max(0.0, best_seen - current_score)

    extra = {
        "per_segment_accuracy": [{"segment_id": sid, "accuracy": acc} for sid, acc in per_seg_acc],
        "routing": routing_stats,
    }
    return asdict(
        EvalResult(
            current_score=float(current_score),
            seen_avg_score=float(seen_avg_score),
            forgetting=float(forgetting),
            num_seen_segments=int(len(segments_seen)),
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
) -> Tuple[float, Dict[str, Any]]:
    correct = 0
    total = 0

    routing_stats = {"num_routed": 0, "branch_counts": {}}

    prompts = [_format_prompt(ex.instruction, ex.input) for ex in segment.eval]
    targets = [ex.output for ex in segment.eval]

    # If router/bank available, route per prompt (simplified hard routing).
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
            # In a real implementation, we'd switch adapter here before generating.
            preds.extend(model.generate([p], max_new_tokens=max_new_tokens))
    else:
        preds = model.generate(prompts, max_new_tokens=max_new_tokens)

    for pred, y in zip(preds, targets):
        total += 1
        if _normalize(pred) == _normalize(y):
            correct += 1

    acc = correct / max(1, total)
    return float(acc), routing_stats


def _merge_routing_stats(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
    dst["num_routed"] += int(src.get("num_routed", 0))
    for k, v in src.get("branch_counts", {}).items():
        dst["branch_counts"][k] = dst["branch_counts"].get(k, 0) + int(v)


def _format_prompt(instruction: str, input_text: str) -> str:
    input_text = (input_text or "").strip()
    if input_text:
        return f"指令：{instruction}\n输入：{input_text}\n输出："
    return f"指令：{instruction}\n输出："


def _normalize(s: str) -> str:
    return (s or "").strip().lower()

