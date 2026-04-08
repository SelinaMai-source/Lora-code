from __future__ import annotations

from typing import Any, Dict, List


def compute_overlap_loss(
    *,
    activations_by_branch: Dict[str, List[List[float]]],
    beta: float,
) -> float:
    """
    Activation diversity / anti-overlap regularization (simplified).

    Intended RP idea:
      - Encourage different LoRA branches to specialize by discouraging highly overlapping
        internal representations on the same anchor/probe set.

    Current simplified proxy:
      - Given per-branch activation vectors for the same prompts, compute average pairwise
        cosine similarity and penalize it:
            loss = beta * mean_{b1<b2} mean_i cos(a[b1,i], a[b2,i])

    Notes:
      - This is model-agnostic and works in debug mode (activations are hashed vectors).
      - In real HF model, activations can be taken from chosen layers/heads.
    """

    if beta <= 0:
        return 0.0

    branches = sorted(list(activations_by_branch.keys()))
    if len(branches) <= 1:
        return 0.0

    # Validate shapes
    n = None
    for b in branches:
        acts = activations_by_branch[b]
        if n is None:
            n = len(acts)
        elif len(acts) != n:
            raise ValueError("All branches must provide activations for the same number of prompts.")

    total = 0.0
    count = 0
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            b1, b2 = branches[i], branches[j]
            sim = _mean_cosine_similarity(activations_by_branch[b1], activations_by_branch[b2])
            total += sim
            count += 1

    mean_sim = total / max(1, count)
    return float(beta * mean_sim)


def compute_overlap_loss_torch(
    *,
    activations_by_branch: Dict[str, "Any"],  # Dict[str, torch.Tensor] shape [B, H]
    beta: float,
) -> "Any":  # torch.Tensor scalar
    """
    Differentiable anti-overlap regularization for training-time integration.

    Expects pooled, L2-normalized activations per prompt:
      activations_by_branch[b] -> Tensor[B, H]
    """
    if beta <= 0:
        import torch

        return torch.tensor(0.0, dtype=torch.float32)

    branches = sorted(list(activations_by_branch.keys()))
    if len(branches) <= 1:
        import torch

        return torch.tensor(0.0, dtype=torch.float32)

    import torch

    # Mean pairwise cosine similarity over prompts and over branch pairs.
    total = torch.tensor(0.0, device=next(iter(activations_by_branch.values())).device)
    count = 0
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            b1, b2 = branches[i], branches[j]
            a1 = activations_by_branch[b1]  # [B, H]
            a2 = activations_by_branch[b2]  # [B, H]
            # Since vectors are L2-normalized, cosine similarity = dot product.
            cos_per_prompt = (a1 * a2).sum(dim=-1)  # [B]
            total = total + cos_per_prompt.mean()
            count += 1
    mean_sim = total / max(1, count)
    return mean_sim * float(beta)


def compute_orthogonal_weight_loss(
    *,
    lora_wrapper: "Any",
    beta: float,
) -> "Any":
    """
    Orthogonal regularization on LoRA weight matrices.
    Penalizes the cosine similarity between the flattened weight vectors of different branches.
    """
    import torch

    if beta <= 0 or lora_wrapper is None or not hasattr(lora_wrapper, "list_adapters"):
        return torch.tensor(0.0, dtype=torch.float32)

    branches = sorted(lora_wrapper.list_adapters())
    if len(branches) <= 1:
        return torch.tensor(0.0, dtype=torch.float32)

    vectors = {}
    for b in branches:
        vec = lora_wrapper.get_adapter_vector(b)
        if vec.numel() > 0:
            vectors[b] = vec

    if len(vectors) <= 1:
        return torch.tensor(0.0, dtype=torch.float32)

    import torch.nn.functional as F

    total = torch.tensor(0.0, device=next(iter(vectors.values())).device)
    count = 0
    branch_list = list(vectors.keys())
    for i in range(len(branch_list)):
        for j in range(i + 1, len(branch_list)):
            b1, b2 = branch_list[i], branch_list[j]
            v1 = vectors[b1]
            v2 = vectors[b2]
            sim = F.cosine_similarity(v1.unsqueeze(0), v2.unsqueeze(0)).squeeze()
            # We want to penalize absolute similarity (both highly correlated and highly anti-correlated)
            # or just positive similarity. Usually, minimizing squared cosine similarity or absolute value.
            total = total + sim.abs()
            count += 1

    mean_sim = total / max(1, count)
    return mean_sim * float(beta)

def _mean_cosine_similarity(a_list: List[List[float]], b_list: List[List[float]]) -> float:
    import math

    sims = []
    for a, b in zip(a_list, b_list):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) + 1e-8
        nb = math.sqrt(sum(y * y for y in b)) + 1e-8
        sims.append(dot / (na * nb))
    return float(sum(sims) / max(1, len(sims)))

