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
    Kalman-Filtered Prototype Router (Telecom/Signal Processing Inspired)
    Tracks task centroids using a Kalman Filter to optimally blend new observations with historical states,
    handling task drift mathematically rigorously without catastrophic forgetting.
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.soft_routing = bool(cfg.get("soft_routing", False))
        self.soft_routing_temperature = float(cfg.get("soft_routing_temperature", 0.1))
        self.soft_routing_top_k = int(cfg.get("soft_routing_top_k", 2))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))
        self.feature_adapter_name = str(cfg.get("feature_adapter_name", "default"))
        
        self.training_strategy = str(cfg.get("training_strategy", "learned_router"))

        self.routing_backend = "kalman"

        # Kalman Filter Parameters
        # Process noise covariance (Q) scalar: how much we expect the true task centroid to drift
        self.kalman_q = float(cfg.get("kalman_q", 1e-4))
        # Measurement noise covariance (R) scalar: how noisy our batch measurements are
        self.kalman_r = float(cfg.get("kalman_r", 1e-2))

        self.nll_arbitration = bool(cfg.get("nll_arbitration", False))
        self.arbitration_margin = float(cfg.get("arbitration_margin", 0.15))
        self.arbitration_top_k = int(cfg.get("arbitration_top_k", 3))
        
        self._prototypes: Dict[str, torch.Tensor] = {} # x_t
        self._P: Dict[str, float] = {} # P_t (scalar for simplicity and stability)
        self._prototype_counts: Dict[str, int] = {}
        
        self._branch_names: List[str] = []
        self._num_updates = 0

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
        frozen_branches: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if len(pseudo_labels) == 0:
            return {"num_router_labels": 0, "router_loss": 0.0, "router_train_acc": 0.0}

        return self._update_prototypes_kalman(
            features=features,
            pseudo_labels=pseudo_labels,
            branch_names=branch_names,
            frozen_branches=frozen_branches or [],
        )

    def _to_feature_tensor(self, features: Any) -> torch.Tensor:
        if isinstance(features, torch.Tensor):
            return features
        if isinstance(features, list) and isinstance(features[0], torch.Tensor):
            return torch.stack(features)
        if isinstance(features, list):
            return torch.tensor(features, dtype=torch.float32)
        return torch.tensor(features, dtype=torch.float32)

    def init_prototype_from_anchor_features(
        self,
        branch_name: str,
        features: Any,
        *,
        sample_count: int,
    ) -> bool:
        feat_t = self._to_feature_tensor(features)
        feat_n = F.normalize(feat_t, p=2, dim=-1)
        proto = F.normalize(feat_n.mean(dim=0), p=2, dim=-1)
        self._prototypes[branch_name] = proto.detach().cpu()
        self._P[branch_name] = self.kalman_r # Initial uncertainty is measurement noise
        self._prototype_counts[branch_name] = max(1, int(sample_count))
        if branch_name not in self._branch_names:
            self._branch_names.append(branch_name)
        return True

    def refresh_prototype_from_anchor_features(
        self,
        branch_name: str,
        features: Any,
        *,
        sample_count: int,
        blend: Optional[float] = None,
    ) -> bool:
        feat_t = self._to_feature_tensor(features)
        feat_n = F.normalize(feat_t, p=2, dim=-1)
        anchor_proto = F.normalize(feat_n.mean(dim=0), p=2, dim=-1)
        
        # Kalman update
        if branch_name in self._prototypes:
            P_pred = self._P[branch_name] + self.kalman_q
            K = P_pred / (P_pred + self.kalman_r)
            
            old = self._prototypes[branch_name].to(anchor_proto.device)
            mixed = old + K * (anchor_proto - old)
            proto = F.normalize(mixed, p=2, dim=-1)
            self._P[branch_name] = (1.0 - K) * P_pred
        else:
            proto = anchor_proto
            self._P[branch_name] = self.kalman_r
            
        self._prototypes[branch_name] = proto.detach().cpu()
        self._prototype_counts[branch_name] = self._prototype_counts.get(branch_name, 0) + max(1, int(sample_count))
        if branch_name not in self._branch_names:
            self._branch_names.append(branch_name)
        return True

    def _update_prototypes_kalman(
        self,
        *,
        features: Any,
        pseudo_labels: List[str],
        branch_names: List[str],
        frozen_branches: List[str],
    ) -> Dict[str, Any]:
        feat_t = self._to_feature_tensor(features)
        feat_n = F.normalize(feat_t, p=2, dim=-1)
        frozen = set(frozen_branches)

        acc = 0.0
        routable = [b for b in branch_names if b in self._prototypes]
        if routable:
            proto_mat = torch.stack([self._prototypes[b].to(feat_n.device) for b in routable])
            sims = feat_n @ proto_mat.T
            preds = [routable[int(i)] for i in torch.argmax(sims, dim=-1)]
            acc = float(sum(1 for p, t in zip(preds, pseudo_labels) if p == t) / len(pseudo_labels))

        num_updated = 0
        for branch in branch_names:
            idx = [i for i, lab in enumerate(pseudo_labels) if lab == branch]
            if not idx:
                continue
            if branch in frozen and branch in self._prototypes:
                continue
                
            batch_mean = F.normalize(feat_n[idx].mean(dim=0), p=2, dim=-1)
            
            if branch not in self._prototypes:
                proto = batch_mean
                self._P[branch] = self.kalman_r
            else:
                # Kalman Filter step
                # Prediction
                P_pred = self._P[branch] + self.kalman_q
                
                # Measurement update
                # R is inversely proportional to batch size to reflect higher confidence in larger batches
                R_effective = self.kalman_r / len(idx)
                K = P_pred / (P_pred + R_effective)
                
                old = self._prototypes[branch].to(batch_mean.device)
                proto = F.normalize(old + K * (batch_mean - old), p=2, dim=-1)
                
                self._P[branch] = (1.0 - K) * P_pred
                
            self._prototypes[branch] = proto.detach().cpu()
            self._prototype_counts[branch] = self._prototype_counts.get(branch, 0) + len(idx)
            num_updated += 1

        for b in branch_names:
            if b not in self._branch_names:
                self._branch_names.append(b)
        self._num_updates += 1
        return {
            "num_router_labels": int(len(pseudo_labels)),
            "router_loss": 0.0,
            "router_ce_loss": 0.0,
            "router_train_acc": float(acc),
            "router_num_prototypes": int(len(self._prototypes)),
            "router_prototypes_updated": int(num_updated),
        }

    def _score_branches(
        self,
        prompt: str,
        branch_names: List[str],
        branch_meta: Dict[str, Any],
        *,
        features: Optional[Any] = None,
    ) -> tuple[Dict[str, float], str]:
        known = [b for b in branch_names if b in self._prototypes]
        if not known:
            latest = branch_names[-1]
            return {b: (1.0 if b == latest else 0.0) for b in branch_names}, "fallback"
            
        feat_t = self._to_feature_tensor(features)
        feat_n = F.normalize(feat_t[0:1], p=2, dim=-1)
        proto_mat = torch.stack([self._prototypes[b].to(feat_n.device) for b in known])
        sims = (feat_n @ proto_mat.T).squeeze(0)
        
        # Softmax over cosine similarities
        probs = F.softmax(sims / 0.1, dim=-1)
        scores = {b: 0.0 for b in branch_names}
        for i, b in enumerate(known):
            scores[b] = float(probs[i].item())
            
        return scores, "kalman_prototype_router"
