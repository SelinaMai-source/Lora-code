from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RoutingDecision:
    branch_name: str
    scores: Dict[str, float]
    hard: bool
    reason: str


class Router:
    """
    Simplified router module for selecting LoRA branches.

    What it should become (future):
      - a small classifier over features (prompt embedding, activation stats, uncertainty)
      - trained with pseudo-labels (e.g., best-performing branch on anchor set)
      - supports soft/hard routing and calibration

    Current implementation:
      - scores branches via a deterministic heuristic: branch age preference + optional string hash
      - exposes hooks for future pseudo-label training
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.pseudo_label_strategy = str(cfg.get("pseudo_label_strategy", "self_consistency"))
        self.temperature = float(cfg.get("temperature", 1.0))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))

        self._num_updates = 0

    def forward(self, prompt: str, branch_names: List[str], branch_meta: Dict[str, Any]) -> RoutingDecision:
        scores = self._score_branches(prompt, branch_names, branch_meta)
        best = max(scores.items(), key=lambda kv: kv[1])[0]
        reason = "argmax_score"
        return RoutingDecision(branch_name=best, scores=scores, hard=self.hard_routing, reason=reason)

    def predict_branch(
        self, *, prompt: str, branch_names: List[str], branch_meta: Dict[str, Any], segment_id: int
    ) -> RoutingDecision:
        if segment_id < self.router_warmup_segments:
            # warmup: always use the latest branch
            latest = branch_names[-1]
            scores = {b: (1.0 if b == latest else 0.0) for b in branch_names}
            return RoutingDecision(
                branch_name=latest,
                scores=scores,
                hard=True,
                reason=f"warmup(<{self.router_warmup_segments})",
            )
        return self.forward(prompt, branch_names, branch_meta)

    def update_with_pseudo_labels(self, batch_prompts: List[str], pseudo_labels: List[str]) -> None:
        # Placeholder hook for future training:
        # - pseudo_labels could be derived from best branch on anchor set
        # - optimize router parameters accordingly
        self._num_updates += 1

    def _score_branches(self, prompt: str, branch_names: List[str], branch_meta: Dict[str, Any]) -> Dict[str, float]:
        # Heuristic: prefer newer branches slightly; add a stable hash-based jitter per prompt
        scores: Dict[str, float] = {}
        base = _stable_hash_float(prompt)
        for i, b in enumerate(branch_names):
            age_bonus = (i + 1) / max(1, len(branch_names))
            scores[b] = 0.7 * age_bonus + 0.3 * base
        return scores

    def state_dict(self) -> Dict[str, Any]:
        return {
            "hard_routing": self.hard_routing,
            "pseudo_label_strategy": self.pseudo_label_strategy,
            "temperature": self.temperature,
            "router_warmup_segments": self.router_warmup_segments,
            "num_updates": self._num_updates,
        }


def _stable_hash_float(s: str) -> float:
    h = 2166136261
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000.0

