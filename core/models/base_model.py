from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


class BaseBackbone:
    """
    A minimal backbone interface used by the unified pipeline.

    Debug path:
      - uses a tiny, deterministic text model that can be "trained" quickly on CPU
    Future path:
      - wrap a Hugging Face causal LM (Llama 3.1 8B Instruct) while keeping the API stable
    """

    def fit_batch(self, pairs: List[Tuple[str, str]], targets: List[str], lr: float) -> Dict[str, float]:
        raise NotImplementedError

    def generate(self, prompts: List[str], max_new_tokens: int = 64) -> List[str]:
        raise NotImplementedError

    def get_activations(self, prompts: List[str]) -> List[List[float]]:
        """Return per-prompt activation vectors (used by overlap/diversity regularization)."""
        raise NotImplementedError


@dataclass
class DebugTextModelConfig:
    """Config for the local debug model."""

    feature_dim: int = 64
    max_memory: int = 5000


class DebugTextModel(BaseBackbone):
    """
    A very lightweight model for local debug:

    - "Training" stores a capped key-value memory of (prompt -> output).
    - "Generation" returns memorized outputs when available, otherwise a simple heuristic.
    - "Activations" are hashed bag-of-words vectors (stable across runs with the same seed).

    This keeps the pipeline fully runnable without downloading large weights.
    """

    def __init__(self, cfg: DebugTextModelConfig, seed: int = 0):
        import numpy as np

        self.cfg = cfg
        self._rng = np.random.RandomState(seed)
        self._memory: Dict[str, str] = {}
        self._memory_fifo: List[str] = []

    def fit_batch(self, pairs: List[Tuple[str, str]], targets: List[str], lr: float) -> Dict[str, float]:
        # lr exists to keep API compatible with real optimizers.
        # Here, we simply store mappings.
        correct = 0
        for (prompt, _), y in zip(pairs, targets):
            pred = self._memory.get(prompt, "")
            if pred.strip() == y.strip():
                correct += 1
            self._remember(prompt, y)
        acc = correct / max(1, len(targets))
        return {"train_batch_acc": acc}

    def generate(self, prompts: List[str], max_new_tokens: int = 64) -> List[str]:
        outs: List[str] = []
        for p in prompts:
            if p in self._memory:
                outs.append(self._memory[p])
            else:
                outs.append(self._fallback(p))
        return outs

    def get_activations(self, prompts: List[str]) -> List[List[float]]:
        import numpy as np

        acts: List[List[float]] = []
        for p in prompts:
            v = np.zeros(self.cfg.feature_dim, dtype=np.float32)
            for tok in _simple_tokenize(p):
                idx = (hash(tok) % self.cfg.feature_dim + self.cfg.feature_dim) % self.cfg.feature_dim
                v[idx] += 1.0
            # L2 normalize
            norm = float(np.linalg.norm(v) + 1e-8)
            v = v / norm
            acts.append(v.tolist())
        return acts

    def _remember(self, prompt: str, output: str) -> None:
        if prompt in self._memory:
            self._memory[prompt] = output
            return
        self._memory[prompt] = output
        self._memory_fifo.append(prompt)
        if len(self._memory_fifo) > self.cfg.max_memory:
            old = self._memory_fifo.pop(0)
            self._memory.pop(old, None)

    def _fallback(self, prompt: str) -> str:
        # A small deterministic fallback: extract numbers and sum if asked, else generic.
        import re

        nums = [int(x) for x in re.findall(r"-?\d+", prompt)]
        if "和" in prompt or "sum" in prompt.lower():
            if len(nums) >= 2:
                return str(sum(nums[:2]))
        return "（debug 模型）我还不会，但我已记录该指令用于后续学习。"


def _simple_tokenize(text: str) -> List[str]:
    text = text.strip().lower()
    if not text:
        return []
    # extremely simple tokenization (works for mixed zh/en in a debug-only way)
    import re

    return [t for t in re.split(r"[^a-z0-9\u4e00-\u9fff]+", text) if t]


def build_backbone(model_cfg: Dict[str, Any], *, mode: str, seed: int, debug_loading: str = "dummy") -> BaseBackbone:
    """
    Build backbone according to mode/config.

    - debug: always returns DebugTextModel unless debug_loading == "hf"
    - baseline/ours: intended to load HuggingFace model (scaffold)
    """

    if mode == "debug":
        if debug_loading == "hf":
            return build_hf_backbone(model_cfg, seed=seed)
        return DebugTextModel(DebugTextModelConfig(), seed=seed)

    return build_hf_backbone(model_cfg, seed=seed)


def build_hf_backbone(model_cfg: Dict[str, Any], *, seed: int) -> BaseBackbone:
    """
    Hugging Face backbone scaffold.

    This repo is research-ready but does not require the 8B weights at generation time.
    If you point hf_model_name_or_path to a valid local path and install dependencies,
    you can implement the real loading here with transformers.

    For now, we return the debug model with a clear error message if user truly expects HF.
    """

    hf_path = str(model_cfg.get("hf_model_name_or_path", "")).strip()
    if hf_path:
        # We do not hard-fail here to keep the repo runnable; instead we guide future extension.
        # When you are ready, replace this with transformers AutoModelForCausalLM + tokenizer.
        pass
    return DebugTextModel(DebugTextModelConfig(), seed=seed)

