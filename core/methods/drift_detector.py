from __future__ import annotations
import math
from typing import Any, Dict, List, Optional
import torch
from dataclasses import dataclass

@dataclass
class DriftEvent:
    triggered: bool
    score: float
    threshold: float
    reason: str

class DriftDetector:
    """
    V15 Information Geometry Drift Detector.
    Uses Bayesian Surprise (Kullback-Leibler divergence between current NLL and historical NLL distribution).
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.warmup_steps = int(cfg.get("warmup_steps", 3)) # Usually segments! So 3 is plenty.
        self.threshold = float(cfg.get("drift_threshold", 3.0))
        self.window_size = int(cfg.get("window_size", 50))
        
        self.history_signal: List[float] = []
        self.current_window: List[float] = []
        self.global_mu = 0.0
        self.global_var = 1.0
        self.step_count = 0

    def update(self, signal: float, segment_id: int) -> DriftEvent:
        self.step_count += 1
        self.current_window.append(signal)
        
        if len(self.current_window) > self.window_size:
            self.current_window.pop(0)
            
        if self.step_count <= self.warmup_steps:
            self.history_signal.append(signal)
            if self.step_count == self.warmup_steps:
                hist_t = torch.tensor(self.history_signal)
                self.global_mu = hist_t.mean().item()
                self.global_var = hist_t.var(unbiased=False).item() + 1e-6
            return DriftEvent(triggered=False, score=0.0, threshold=self.threshold, reason="warmup")
            
        window_t = torch.tensor(self.current_window)
        win_mu = window_t.mean().item()
        win_var = window_t.var(unbiased=False).item() + 1e-6
        
        # Calculate KL divergence KL(Window || Global)
        # KL(N0 || N1) = 0.5 * (var0/var1 + (mu1-mu0)^2/var1 - 1 + ln(var1/var0))
        kl_div = 0.5 * (win_var / self.global_var + ((self.global_mu - win_mu)**2) / self.global_var - 1 + math.log(max(self.global_var / win_var, 1e-10)))
        
        # Bayesian surprise
        if kl_div > self.threshold:
            self._reset_stats()
            return DriftEvent(triggered=True, score=kl_div, threshold=self.threshold, reason="bayesian_surprise_drift")
            
        # Exponential moving average update for global
        self.global_mu = 0.99 * self.global_mu + 0.01 * signal
        return DriftEvent(triggered=False, score=kl_div, threshold=self.threshold, reason="stable")

    def _reset_stats(self):
        self.step_count = 0
        self.history_signal = []
        self.current_window = []
        
    def state_dict(self) -> Dict[str, Any]:
        return {
            "global_mu": self.global_mu,
            "global_var": self.global_var,
            "step_count": self.step_count,
            "history_signal": self.history_signal,
            "current_window": self.current_window
        }
        
    def load_state_dict(self, state_dict: Dict[str, Any]):
        self.global_mu = state_dict.get("global_mu", 0.0)
        self.global_var = state_dict.get("global_var", 1.0)
        self.step_count = state_dict.get("step_count", 0)
        self.history_signal = state_dict.get("history_signal", [])
        self.current_window = state_dict.get("current_window", [])
