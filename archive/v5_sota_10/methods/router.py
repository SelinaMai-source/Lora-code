from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class RoutingDecision:
    branch_name: str
    scores: Dict[str, float]
    hard: bool
    reason: str


class Router:
    """
    Navier-Stokes Incompressible Flow Router
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.soft_routing = bool(cfg.get("soft_routing", False))
        self.soft_routing_temperature = float(cfg.get("soft_routing_temperature", 0.1))
        self.soft_routing_top_k = int(cfg.get("soft_routing_top_k", 2))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))
        self.feature_adapter_name = str(cfg.get("feature_adapter_name", "default"))
        
        self.temperature = float(cfg.get("temperature", 1.0))
        self.learning_rate = float(cfg.get("learning_rate", 0.001))
        
        # PID Controller parameters
        self.pid_enabled = bool(cfg.get("pid_enabled", True))
        self.kp = float(cfg.get("pid_kp", 0.1))
        self.ki = float(cfg.get("pid_ki", 0.01))
        self.kd = float(cfg.get("pid_kd", 0.05))
        self.training_strategy = str(cfg.get("training_strategy", "learned_router"))
        
        self.fluid_lambda = float(cfg.get("fluid_lambda", 0.1))
        self.fluid_gamma = float(cfg.get("fluid_gamma", 0.01))

        self._num_updates = 0
        self._branch_names: List[str] = []
        
        self._head: Optional[torch.nn.Linear] = None
        self._optimizer: Optional[torch.optim.Optimizer] = None
        
        # PID state
        self._integral_error: Optional[torch.Tensor] = None
        self._prev_error: Optional[torch.Tensor] = None
        self._historical_prob: Optional[torch.Tensor] = None

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
            [branch_names.index(label) for label in pseudo_labels],
            dtype=torch.long,
            device=feat_t.device,
        )
        
        logits = self._project_logits(feat_t, branch_names)
        ce_loss = F.cross_entropy(logits, target_idx)
        
        # Fluid mechanics divergence penalty (Incompressible Flow)
        prob = F.softmax(logits, dim=-1)
        fluid_flow = prob.mean(dim=0)
        target_flow = torch.ones_like(fluid_flow) / max(1, len(branch_names))
        divergence_loss = F.mse_loss(fluid_flow, target_flow)
        
        loss = ce_loss + self.fluid_lambda * divergence_loss
        
        if self.fluid_gamma > 0.0:
            variance_penalty = prob.var(dim=0).mean()
            loss = loss + self.fluid_gamma * variance_penalty

        self._optimizer.zero_grad(set_to_none=True)
        loss.backward()
        self._optimizer.step()

        with torch.no_grad():
            preds = torch.argmax(logits, dim=-1)
            acc = float((preds == target_idx).float().mean().item())
            
            # Update historical prob
            if self.pid_enabled:
                prob_all = F.softmax(self._head(feat_t), dim=-1)
                current_prob = prob_all.mean(dim=0)
                if self._historical_prob is None:
                    self._historical_prob = current_prob
                else:
                    # Exponential moving average
                    alpha = 0.1
                    if len(self._historical_prob) < len(current_prob):
                        new_hist = torch.zeros_like(current_prob)
                        new_hist[:len(self._historical_prob)] = self._historical_prob
                        self._historical_prob = new_hist
                    self._historical_prob = (1 - alpha) * self._historical_prob + alpha * current_prob

        self._num_updates += 1
        return {
            "num_router_labels": int(len(pseudo_labels)),
            "router_loss": float(loss.detach().item()),
            "router_ce_loss": float(ce_loss.detach().item()),
            "router_train_acc": float(acc),
        }

    def _ensure_head(self, features: torch.Tensor, branch_names: List[str]) -> None:
        feat_dim = int(features.shape[-1])
        device = features.device
        if self._head is None:
            self._branch_names = list(branch_names)
            self._head = nn.Linear(feat_dim, len(self._branch_names), bias=True).to(device)
            self._optimizer = torch.optim.AdamW(self._head.parameters(), lr=self.learning_rate)
            return

        if int(self._head.in_features) != feat_dim:
            raise ValueError(
                f"Router feature dim changed from {self._head.in_features} to {feat_dim}"
            )

        missing = [b for b in branch_names if b not in self._branch_names]
        if not missing:
            return

        old_head = self._head
        new_branch_names = list(self._branch_names) + missing
        new_head = nn.Linear(feat_dim, len(new_branch_names), bias=True).to(device)
        with torch.no_grad():
            new_head.weight.zero_()
            new_head.bias.zero_()
            new_head.weight[: old_head.out_features] = old_head.weight.data
            new_head.bias[: old_head.out_features] = old_head.bias.data
        self._head = new_head
        self._branch_names = new_branch_names
        self._optimizer = torch.optim.AdamW(self._head.parameters(), lr=self.learning_rate)

    def _project_logits(self, features: torch.Tensor, branch_names: List[str]) -> torch.Tensor:
        if self._head is None:
            raise RuntimeError("Router head is not initialized.")
        logits_all = self._head(features)
        indices = [self._branch_names.index(name) for name in branch_names]
        logits = logits_all[:, indices]
        
        # Apply PID correction if enabled
        if self.pid_enabled and self._historical_prob is not None:
            prob = F.softmax(logits, dim=-1)
            current_prob = prob.mean(dim=0)
            
            # Map historical prob to current branches
            hist_prob = torch.zeros_like(current_prob)
            for i, b in enumerate(branch_names):
                if b in self._branch_names:
                    idx = self._branch_names.index(b)
                    if idx < len(self._historical_prob):
                        hist_prob[i] = self._historical_prob[idx]
            
            # Normalize hist_prob
            if hist_prob.sum() > 0:
                hist_prob = hist_prob / hist_prob.sum()
            else:
                hist_prob = torch.ones_like(hist_prob) / len(branch_names)
                
            error = hist_prob - current_prob
            
            if self._integral_error is None or len(self._integral_error) != len(branch_names):
                self._integral_error = torch.zeros_like(error)
                self._prev_error = torch.zeros_like(error)
                
            self._integral_error += error
            derivative = error - self._prev_error
            
            pid_correction = self.kp * error + self.ki * self._integral_error + self.kd * derivative
            logits = logits + pid_correction.unsqueeze(0)
            self._prev_error = error
            
        return logits

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
            
            # Apply a physical decay factor (Tsallis entropy inspired softmax from statistical physics)
            # This provides a heavy-tailed distribution to prevent expert collapse
            q = 1.5
            temp = max(1e-6, self.temperature)
            scaled_logits = logits[0] / temp
            max_logit = torch.max(scaled_logits)
            # Tsallis q-exponential: exp_q(x) = [1 + (1-q)x]^(1/(1-q))
            tsallis_exp = torch.relu(1.0 + (1.0 - q) * (scaled_logits - max_logit)) ** (1.0 / (1.0 - q))
            probs = tsallis_exp / torch.sum(tsallis_exp)
            
            scores = {b: float(probs[i].item()) for i, b in enumerate(branch_names)}
            
            if self.soft_routing:
                import math
                valid_scores = {b: s for b, s in scores.items() if s > 0.01}
                if len(valid_scores) > 0:
                    max_score = max(valid_scores.values())
                    exp_scores = {b: math.exp((s - max_score) / self.soft_routing_temperature) for b, s in valid_scores.items()}
                    top_k = self.soft_routing_top_k
                    top_k_items = sorted(exp_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
                    top_k_branches = set(b for b, v in top_k_items)
                    for b in list(exp_scores.keys()):
                        if b not in top_k_branches:
                            exp_scores[b] = 0.0
                    
                    total_exp = sum(exp_scores.values())
                    if total_exp > 0:
                        scores = {b: (exp_scores.get(b, 0.0) / total_exp) for b in branch_names}

            return scores, "pid_router"

        scores: Dict[str, float] = {}
        base = _stable_hash_float(prompt)
        for i, b in enumerate(branch_names):
            age_bonus = (i + 1) / max(1, len(branch_names))
            scores[b] = 0.7 * age_bonus + 0.3 * base
        return scores, "heuristic_router"

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
            "router_warmup_segments": self.router_warmup_segments,
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
