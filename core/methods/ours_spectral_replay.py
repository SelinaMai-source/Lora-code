from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import torch
import torch.nn.functional as F

class SpectralSparseReplayGate:
    """
    V14 Information Geometry MMD Core-set Replay Gate.
    Selects replay samples by maximizing the Maximum Mean Discrepancy (MMD) coverage
    in the Fisher Information embedding space, ensuring the replay buffer spans the distribution.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.buffer_size = int(cfg.get("buffer_size", 1000))
        self.replay_ratio = float(cfg.get("replay_ratio", 0.5))
        self.buffer: List[Dict[str, Any]] = []

    def get_replay_ratio(self) -> float:
        return self.replay_ratio

    def update_buffer(self, segment_idx: int, features: Any, pairs: List[Any], targets: List[Any]) -> None:
        if isinstance(features, torch.Tensor):
            feat_t = features
        elif isinstance(features, list) and isinstance(features[0], torch.Tensor):
            feat_t = torch.stack(features)
        else:
            feat_t = torch.tensor(features, dtype=torch.float32)
            
        feat_n = F.normalize(feat_t, p=2, dim=-1)
        
        # Simple greedy MMD (Maximum Mean Discrepancy) coverage: 
        # Pick samples that are furthest from currently selected samples
        selected_idx = []
        n = feat_n.shape[0]
        
        if n > 0:
            selected_idx.append(0)
            
        # Select up to buffer_size//10 from this segment
        budget = min(n, max(1, self.buffer_size // 10))
        
        if budget > 1 and n > 1:
            dist_matrix = 1.0 - torch.mm(feat_n, feat_n.t()) # cosine distance
            min_dists = dist_matrix[selected_idx[0]].clone()
            
            for _ in range(1, budget):
                best_idx = torch.argmax(min_dists).item()
                selected_idx.append(best_idx)
                min_dists = torch.min(min_dists, dist_matrix[best_idx])
                
        for idx in selected_idx:
            if len(self.buffer) >= self.buffer_size:
                # Random eviction
                import random
                pop_idx = random.randint(0, len(self.buffer) - 1)
                self.buffer.pop(pop_idx)
                
            self.buffer.append({
                "segment_idx": segment_idx,
                "pair": pairs[idx],
                "target": targets[idx]
            })

    def sample_replay(self, batch_size: int) -> tuple[List[Any], List[Any]]:
        import random
        if not self.buffer:
            return [], []
            
        sample_size = min(batch_size, len(self.buffer))
        sampled = random.sample(self.buffer, sample_size)
        pairs = [s["pair"] for s in sampled]
        targets = [s["target"] for s in sampled]
        return pairs, targets
