from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math
import hashlib

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
    V16 Semantic Hashing Router with Quantum Bures Metric.
    Maps representations to a statistical manifold using semantic character n-grams.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.hard_routing = bool(cfg.get("hard_routing", True))
        self.router_warmup_segments = int(cfg.get("router_warmup_segments", 1))
        self.prototype_ema = float(cfg.get("prototype_ema", 0.8))
        
        self._mu: Dict[str, torch.Tensor] = {} # Mean of features for the branch
        self._var: Dict[str, torch.Tensor] = {} # Variance of features
        self._prototype_counts: Dict[str, int] = {}
        self._branch_names: List[str] = []
        self._num_updates = 0

    def _get_pseudo_features(self, prompt: str) -> torch.Tensor:
        # Use character trigram feature hashing for semantic pseudo-features
        dim = 256
        feat = torch.zeros(dim)
        prompt = prompt.lower()
        for i in range(max(1, len(prompt) - 2)):
            trigram = prompt[i:i+3]
            # Use md5 to get a stable hash across Python runs (built-in hash() is randomized)
            h = int(hashlib.md5(trigram.encode('utf-8')).hexdigest(), 16) % dim
            feat[h] += 1.0
        return feat

    def _bures_metric(self, mu1, var1, mu2, var2):
        """
        Computes Bures metric (Quantum Fidelity) between two diagonal Gaussian distributions.
        D_B^2 = ||m1 - m2||_2^2 + Tr(S1 + S2 - 2(S1^0.5 S2 S1^0.5)^0.5)
        For diagonal matrices, this is equivalent to Wasserstein, but we scale it differently.
        """
        diff_mu = torch.sum((mu1 - mu2) ** 2, dim=-1)
        diff_var = torch.sum(var1 + var2 - 2 * torch.sqrt(var1 * var2.clamp_min(1e-8)), dim=-1)
        return diff_mu + diff_var

    def predict_branch(self, prompt: str, branch_names: List[str], branch_meta: Dict[str, Any], segment_id: int = 0, **kwargs) -> RoutingDecision:
        latest = branch_names[-1]
        if len(branch_names) <= self.router_warmup_segments:
            scores = {b: (1.0 if b == latest else 0.0) for b in branch_names}
            return RoutingDecision(branch_name=latest, scores=scores, hard=True, reason=f"warmup(<{self.router_warmup_segments})")
            
        feat_n = F.normalize(self._get_pseudo_features(prompt), p=2, dim=-1)
        
        routable = [b for b in branch_names if b in self._mu]
        if not routable:
            return RoutingDecision(branch_name=latest, scores={}, hard=True, reason="no_prototypes")

        scores = {}
        best_b = routable[0]
        min_dist = float('inf')
        
        # Treat input as a Dirac delta (var -> 0) or small variance
        input_var = torch.full_like(feat_n, 1e-6)
        
        for b in routable:
            mu_b = self._mu[b].to(feat_n.device)
            var_b = self._var[b].to(feat_n.device)
            
            dist = self._bures_metric(feat_n, input_var, mu_b, var_b).item()
            score = -dist # Lower distance is better score
            scores[b] = score
            if dist < min_dist:
                min_dist = dist
                best_b = b

        return RoutingDecision(branch_name=best_b, scores=scores, hard=True, reason="bures_routing")

    def update_with_pseudo_labels(self, batch_prompts: List[str], pseudo_labels: List[str], branch_names: List[str] = None, frozen_branches: Optional[List[str]] = None) -> Dict[str, Any]:
        if len(pseudo_labels) == 0:
            return {"num_router_labels": 0, "router_loss": 0.0, "router_train_acc": 0.0}
            
        frozen = set(frozen_branches or [])
        if branch_names is None:
            branch_names = list(set(pseudo_labels))
            
        num_updated = 0
        for branch in branch_names:
            idx = [i for i, lab in enumerate(pseudo_labels) if lab == branch]
            if not idx:
                continue
            if branch in frozen and branch in self._mu:
                continue
                
            batch_feat = torch.stack([F.normalize(self._get_pseudo_features(batch_prompts[i]), p=2, dim=-1) for i in idx])
            batch_mu = batch_feat.mean(dim=0)
            batch_var = batch_feat.var(dim=0, unbiased=False) if len(idx) > 1 else torch.full_like(batch_mu, 1e-4)
            
            if branch not in self._mu:
                self._mu[branch] = batch_mu.detach().cpu()
                self._var[branch] = batch_var.detach().cpu().clamp(min=1e-6)
            else:
                old_mu = self._mu[branch].to(batch_mu.device)
                old_var = self._var[branch].to(batch_mu.device)
                
                ema = self.prototype_ema
                new_mu = ema * old_mu + (1 - ema) * batch_mu
                # Variance update (approximate for mixture)
                new_var = ema * old_var + (1 - ema) * batch_var + ema * (1 - ema) * (old_mu - batch_mu)**2
                
                self._mu[branch] = new_mu.detach().cpu()
                self._var[branch] = new_var.detach().cpu().clamp(min=1e-6)
                
            self._prototype_counts[branch] = self._prototype_counts.get(branch, 0) + len(idx)
            if branch not in self._branch_names:
                self._branch_names.append(branch)
            num_updated += 1
            
        self._num_updates += 1
        return {"num_router_labels": len(pseudo_labels), "router_loss": 0.0, "router_train_acc": 1.0}

    def state_dict(self) -> Dict[str, Any]:
        return {
            "mu": {k: v.clone().tolist() for k, v in self._mu.items()},
            "var": {k: v.clone().tolist() for k, v in self._var.items()},
            "prototype_counts": self._prototype_counts.copy(),
            "branch_names": list(self._branch_names),
            "num_updates": self._num_updates,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        self._mu = {k: torch.tensor(v, dtype=torch.float32) for k, v in state_dict.get("mu", {}).items()}
        self._var = {k: torch.tensor(v, dtype=torch.float32) for k, v in state_dict.get("var", {}).items()}
        self._prototype_counts = state_dict.get("prototype_counts", {}).copy()
        self._branch_names = list(state_dict.get("branch_names", []))
        self._num_updates = state_dict.get("num_updates", 0)
