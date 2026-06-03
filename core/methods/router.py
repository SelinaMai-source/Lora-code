from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import torch
import torch.nn.functional as F


@dataclass
class RoutingDecision:
    branch_name: str
    scores: Dict[str, float]
    hard: bool
    reason: str


class Router:
    """
    Lightweight router trained with pseudo-labels over prompt features.

    Behavior:
      - Warmup: route to the latest branch
      - If a learned head is available and features are supplied, predict with the classifier
      - Otherwise fall back to the deterministic heuristic used by the early prototype
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.pseudo_label_strategy = str(cfg.get("pseudo_label_strategy", "self_consistency"))
        self.temperature = float(cfg.get("temperature", 1.0))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))
        self.learning_rate = float(cfg.get("learning_rate", 1.0e-3))
        self.weight_decay = float(cfg.get("weight_decay", 0.0))
        self.margin_filter_min_gap = float(cfg.get("margin_filter_min_gap", 0.05))
        self.feature_adapter_name = str(cfg.get("feature_adapter_name", "default"))
        self.training_strategy = str(cfg.get("training_strategy", "active_branch")).strip() or "active_branch"
        self.training_fallback_to_active = bool(cfg.get("training_fallback_to_active", True))
        self.train_frozen_branches = bool(cfg.get("train_frozen_branches", False))
        self.balance_beta = float(cfg.get("balance_beta", 0.0))
        self.orthogonal_head_beta = float(cfg.get("orthogonal_head_beta", 0.0))

        self._num_updates = 0
        self._branch_names: List[str] = []
        self._head: Optional[torch.nn.Linear] = None
        self._optimizer: Optional[torch.optim.Optimizer] = None

    def forward(
        self,
        prompt: str,
        branch_names: List[str],
        branch_meta: Dict[str, Any],
        *,
        features: Optional[Any] = None,
    ) -> RoutingDecision:
        scores, reason = self._score_branches(prompt, branch_names, branch_meta, features=features)
        best = max(scores.items(), key=lambda kv: kv[1])[0]
        return RoutingDecision(branch_name=best, scores=scores, hard=self.hard_routing, reason=reason)

    def predict_branch(
        self,
        *,
        prompt: str,
        branch_names: List[str],
        branch_meta: Dict[str, Any],
        segment_id: int,
        features: Optional[Any] = None,
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
        return self.forward(prompt, branch_names, branch_meta, features=features)

    def update_with_pseudo_labels(
        self,
        *,
        features: Any,
        pseudo_labels: List[str],
        branch_names: List[str],
    ) -> Dict[str, Any]:
        if len(pseudo_labels) == 0:
            return {"num_router_labels": 0, "router_loss": 0.0, "router_train_acc": 0.0}
        feat_t = self._to_feature_tensor(features)
        self._ensure_head(feat_t, branch_names)
        if self._head is None or self._optimizer is None:
            return {"num_router_labels": 0, "router_loss": 0.0, "router_train_acc": 0.0}

        target_idx = torch.tensor(
            [self._branch_names.index(label) for label in pseudo_labels],
            dtype=torch.long,
            device=feat_t.device,
        )
        logits = self._project_logits(feat_t, branch_names)
        ce_loss = F.cross_entropy(logits, target_idx)
        probs = torch.softmax(logits, dim=-1)
        balance_loss = self._balance_loss(probs)
        orthogonal_loss = self._orthogonal_head_loss(branch_names)
        loss = ce_loss + self.balance_beta * balance_loss + self.orthogonal_head_beta * orthogonal_loss

        self._optimizer.zero_grad(set_to_none=True)
        loss.backward()
        self._optimizer.step()

        with torch.no_grad():
            preds = torch.argmax(logits, dim=-1)
            acc = float((preds == target_idx).float().mean().item())

        self._num_updates += 1
        return {
            "num_router_labels": int(len(pseudo_labels)),
            "router_loss": float(loss.detach().item()),
            "router_ce_loss": float(ce_loss.detach().item()),
            "router_balance_loss": float(balance_loss.detach().item()),
            "router_orthogonal_head_loss": float(orthogonal_loss.detach().item()),
            "router_train_acc": float(acc),
        }

    def _balance_loss(self, probs: torch.Tensor) -> torch.Tensor:
        if self.balance_beta <= 0 or probs.numel() == 0:
            return torch.tensor(0.0, dtype=torch.float32, device=probs.device)
        mean_probs = probs.mean(dim=0)
        target = torch.full_like(mean_probs, 1.0 / max(1, mean_probs.numel()))
        return F.mse_loss(mean_probs, target)

    def _orthogonal_head_loss(self, branch_names: List[str]) -> torch.Tensor:
        if self.orthogonal_head_beta <= 0 or self._head is None or len(branch_names) <= 1:
            device = self._head.weight.device if self._head is not None else torch.device("cpu")
            return torch.tensor(0.0, dtype=torch.float32, device=device)
        indices = [self._branch_names.index(name) for name in branch_names]
        rows = F.normalize(self._head.weight[indices], dim=-1)
        gram = rows @ rows.T
        eye = torch.eye(len(indices), dtype=gram.dtype, device=gram.device)
        return ((gram - eye) ** 2).mean()

    def _score_branches(
        self,
        prompt: str,
        branch_names: List[str],
        branch_meta: Dict[str, Any],
        *,
        features: Optional[Any] = None,
    ) -> tuple[Dict[str, float], str]:
        if features is not None and self._head is not None and set(branch_names).issubset(set(self._branch_names)):
            feat_t = self._to_feature_tensor(features)
            logits = self._project_logits(feat_t, branch_names)
            probs = torch.softmax(logits[0] / max(1e-6, self.temperature), dim=-1)
            return ({b: float(probs[i].item()) for i, b in enumerate(branch_names)}, "learned_router")

        # Heuristic fallback: prefer newer branches slightly; add a stable hash-based jitter per prompt
        scores: Dict[str, float] = {}
        base = _stable_hash_float(prompt)
        for i, b in enumerate(branch_names):
            age_bonus = (i + 1) / max(1, len(branch_names))
            scores[b] = 0.7 * age_bonus + 0.3 * base
        return scores, "heuristic_router"

    def _ensure_head(self, features: torch.Tensor, branch_names: List[str]) -> None:
        feat_dim = int(features.shape[-1])
        device = features.device
        if self._head is None:
            self._branch_names = list(branch_names)
            self._head = torch.nn.Linear(feat_dim, len(self._branch_names), bias=True).to(device)
            self._optimizer = torch.optim.AdamW(
                self._head.parameters(),
                lr=self.learning_rate,
                weight_decay=self.weight_decay,
            )
            return

        if int(self._head.in_features) != feat_dim:
            raise ValueError(
                f"Router feature dim changed from {self._head.in_features} to {feat_dim}; "
                "use a consistent feature extractor."
            )

        missing = [b for b in branch_names if b not in self._branch_names]
        if not missing:
            return

        old_head = self._head
        new_branch_names = list(self._branch_names) + missing
        new_head = torch.nn.Linear(feat_dim, len(new_branch_names), bias=True).to(device)
        with torch.no_grad():
            new_head.weight.zero_()
            new_head.bias.zero_()
            new_head.weight[: old_head.out_features] = old_head.weight.data
            new_head.bias[: old_head.out_features] = old_head.bias.data
        self._head = new_head
        self._branch_names = new_branch_names
        self._optimizer = torch.optim.AdamW(
            self._head.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

    def _project_logits(self, features: torch.Tensor, branch_names: List[str]) -> torch.Tensor:
        if self._head is None:
            raise RuntimeError("Router head is not initialized.")
        logits_all = self._head(features)
        indices = [self._branch_names.index(name) for name in branch_names]
        return logits_all[:, indices]

    def _to_feature_tensor(self, features: Any) -> torch.Tensor:
        if isinstance(features, torch.Tensor):
            feat_t = features
        else:
            feat_t = torch.tensor(features, dtype=torch.float32)
        if feat_t.dim() == 1:
            feat_t = feat_t.unsqueeze(0)
        if self._head is not None:
            feat_t = feat_t.to(self._head.weight.device)
        return feat_t.to(torch.float32)

    def state_dict(self) -> Dict[str, Any]:
        state = {
            "hard_routing": self.hard_routing,
            "pseudo_label_strategy": self.pseudo_label_strategy,
            "temperature": self.temperature,
            "router_warmup_segments": self.router_warmup_segments,
            "training_strategy": self.training_strategy,
            "training_fallback_to_active": self.training_fallback_to_active,
            "train_frozen_branches": self.train_frozen_branches,
            "balance_beta": self.balance_beta,
            "orthogonal_head_beta": self.orthogonal_head_beta,
            "num_updates": self._num_updates,
            "branch_names": list(self._branch_names),
            "feature_adapter_name": self.feature_adapter_name,
        }
        if self._head is not None:
            state["head"] = {
                "in_features": int(self._head.in_features),
                "out_features": int(self._head.out_features),
                "weight": self._head.weight.detach().cpu().tolist(),
                "bias": self._head.bias.detach().cpu().tolist(),
            }
        return state


def _stable_hash_float(s: str) -> float:
    h = 2166136261
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000.0

