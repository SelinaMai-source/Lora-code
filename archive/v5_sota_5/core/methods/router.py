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
    Variational Information Bottleneck (VIB) Router
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.soft_routing = bool(cfg.get("soft_routing", False))
        self.soft_routing_temperature = float(cfg.get("soft_routing_temperature", 0.1))
        self.soft_routing_top_k = int(cfg.get("soft_routing_top_k", 2))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))
        self.feature_adapter_name = str(cfg.get("feature_adapter_name", "default"))
        
        self.temperature = float(cfg.get("temperature", 0.1))
        self.vib_beta = float(cfg.get("vib_beta", 0.01))
        self.learning_rate = float(cfg.get("learning_rate", 0.01))
        self.training_strategy = str(cfg.get("training_strategy", "learned_router"))

        self._num_updates = 0
        self._branch_names: List[str] = []
        
        # Prototypes as learnable parameters
        self._prototypes: Dict[str, torch.Tensor] = {}
        
        # Router Replay Buffer
        self.replay_buffer_size = int(cfg.get("replay_buffer_size", 2000))
        self._replay_features: List[torch.Tensor] = []
        self._replay_labels: List[str] = []

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
        
        for b in branch_names:
            if b not in self._branch_names:
                self._branch_names.append(b)
                
        for i, label in enumerate(pseudo_labels):
            self._replay_features.append(feat_t[i].detach().cpu())
            self._replay_labels.append(label)
            
        if len(self._replay_features) > self.replay_buffer_size:
            excess = len(self._replay_features) - self.replay_buffer_size
            self._replay_features = self._replay_features[excess:]
            self._replay_labels = self._replay_labels[excess:]
            
        # Initialize missing prototypes
        for label in set(self._replay_labels):
            if label not in self._prototypes:
                feats = [f for f, l in zip(self._replay_features, self._replay_labels) if l == label]
                if feats:
                    mean_feat = torch.stack(feats).mean(dim=0)
                    self._prototypes[label] = F.normalize(mean_feat, p=2, dim=0).to(feat_t.device).requires_grad_(True)

        params = []
        for k, v in self._prototypes.items():
            if v.device != feat_t.device:
                self._prototypes[k] = v.to(feat_t.device).detach().requires_grad_(True)
            elif not v.requires_grad:
                self._prototypes[k] = v.detach().requires_grad_(True)
            params.append(self._prototypes[k])

        if not params:
            return {"num_router_labels": 0, "router_loss": 0.0, "router_train_acc": 0.0}

        optimizer = torch.optim.Adam(params, lr=self.learning_rate)
        
        epochs = 5
        batch_size = 64
        total_loss = 0.0
        
        dataset_size = len(self._replay_features)
        indices = list(range(dataset_size))
        
        for _ in range(epochs):
            import random
            random.shuffle(indices)
            for i in range(0, dataset_size, batch_size):
                batch_idx = indices[i:i+batch_size]
                batch_feats = torch.stack([self._replay_features[idx] for idx in batch_idx]).to(feat_t.device)
                batch_labels = [self._replay_labels[idx] for idx in batch_idx]
                
                batch_feats = F.normalize(batch_feats, p=2, dim=1)
                
                logits = []
                for b in self._branch_names:
                    if b in self._prototypes:
                        p = F.normalize(self._prototypes[b], p=2, dim=0)
                        sim = F.linear(batch_feats, p.unsqueeze(0)).squeeze(1)
                        logits.append(sim / self.temperature)
                    else:
                        logits.append(torch.full((len(batch_idx),), -100.0, device=feat_t.device))
                
                logits = torch.stack(logits, dim=1) # [B, num_branches]
                targets = torch.tensor([self._branch_names.index(l) for l in batch_labels], device=feat_t.device)
                
                ce_loss = F.cross_entropy(logits, targets)
                
                # Variational Information Bottleneck (VIB) for Prototypes
                proto_list = list(self._prototypes.values())
                if len(proto_list) > 1:
                    protos = torch.stack(proto_list)
                    protos_norm = F.normalize(protos, p=2, dim=1)
                    
                    # Estimate variance from replay buffer
                    kl_loss = torch.tensor(0.0, device=feat_t.device)
                    for b_idx, b in enumerate(self._prototypes.keys()):
                        b_feats = [self._replay_features[idx] for idx in range(dataset_size) if self._replay_labels[idx] == b]
                        if len(b_feats) > 1:
                            b_feats_t = torch.stack(b_feats).to(feat_t.device)
                            b_feats_norm = F.normalize(b_feats_t, p=2, dim=1)
                            mu = b_feats_norm.mean(dim=0)
                            var = b_feats_norm.std(dim=0).pow(2) + 1e-6
                            log_var = torch.log(var)
                            kl_loss += -0.5 * torch.sum(1 + log_var - mu.pow(2) - var)
                    kl_loss = kl_loss / max(1, len(self._prototypes))
                    
                    proto_loss = self.vib_beta * kl_loss
                else:
                    proto_loss = torch.tensor(0.0, device=feat_t.device)
                
                loss = ce_loss + proto_loss
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()

        acc = 0.0
        with torch.no_grad():
            preds = []
            for i, label in enumerate(pseudo_labels):
                z = F.normalize(feat_t[i], p=2, dim=0).unsqueeze(0)
                best_sim = -float('inf')
                best_branch = label
                for b, p in self._prototypes.items():
                    p_norm = F.normalize(p, p=2, dim=0)
                    sim = F.cosine_similarity(z, p_norm.unsqueeze(0)).item()
                    if sim > best_sim:
                        best_sim = sim
                        best_branch = b
                preds.append(1 if best_branch == label else 0)
            acc = sum(preds) / max(1, len(preds))

        self._num_updates += 1
        return {
            "num_router_labels": int(len(pseudo_labels)),
            "router_loss": float(total_loss),
            "router_ce_loss": float(total_loss),
            "router_balance_loss": 0.0,
            "router_orthogonal_head_loss": float(proto_loss) if 'proto_loss' in locals() else 0.0,
            "router_train_acc": float(acc),
        }

    def _score_branches(
        self,
        prompt: str,
        branch_names: List[str],
        branch_meta: Dict[str, Any],
        *,
        features: Optional[Any] = None,
    ) -> tuple[Dict[str, float], str]:
        if features is not None and len(self._prototypes) > 0:
            feat_t = self._to_feature_tensor(features)
            z = F.normalize(feat_t[0], p=2, dim=0).unsqueeze(0)
            scores = {}
            for b in branch_names:
                if b in self._prototypes:
                    p = F.normalize(self._prototypes[b], p=2, dim=0).unsqueeze(0).to(z.device)
                    sim = F.cosine_similarity(z, p).item()
                    scores[b] = sim
                else:
                    scores[b] = -1.0
                    
            if self.soft_routing:
                import math
                valid_scores = {b: s for b, s in scores.items() if s > -0.99}
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

            return scores, "vib_router"

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
        return feat_t.to(torch.float32)

    def state_dict(self) -> Dict[str, Any]:
        state = {
            "hard_routing": self.hard_routing,
            "router_warmup_segments": self.router_warmup_segments,
            "num_updates": self._num_updates,
            "branch_names": list(self._branch_names),
            "feature_adapter_name": self.feature_adapter_name,
            "prototypes": {k: v.tolist() for k, v in self._prototypes.items()}
        }
        return state


def _stable_hash_float(s: str) -> float:
    h = 2166136261
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 1000) / 1000.0
