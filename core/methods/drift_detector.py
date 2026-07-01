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
    V16 Thermodynamic Free Energy Drift Detector.
    Uses Free Energy Principle (F = E - T*S) to detect distribution shifts.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.warmup_steps = int(cfg.get("warmup_steps", 1)) # Reduced to 1 for faster adaptation
        self.threshold = float(cfg.get("drift_threshold", 1.5))
        self.window_size = int(cfg.get("window_size", 50))
        self.temperature = float(cfg.get("temperature", 1.0))
        
        self.history_signal: List[float] = []
        self.current_window: List[float] = []
        self.global_energy = 0.0
        self.global_entropy = 1.0
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
                self.global_energy = hist_t.mean().item()
                self.global_entropy = hist_t.var(unbiased=False).item() + 1e-6
            return DriftEvent(triggered=False, score=0.0, threshold=self.threshold, reason="warmup")
            
        window_t = torch.tensor(self.current_window)
        win_energy = window_t.mean().item()
        win_entropy = window_t.var(unbiased=False).item() + 1e-6
        
        # Calculate Free Energy difference: Delta F = Delta E - T * Delta S
        delta_e = abs(win_energy - self.global_energy)
        delta_s = abs(math.log(win_entropy) - math.log(self.global_entropy))
        free_energy_diff = delta_e + self.temperature * delta_s
        
        if free_energy_diff > self.threshold:
            self._reset_stats()
            return DriftEvent(triggered=True, score=free_energy_diff, threshold=self.threshold, reason="thermodynamic_drift")
            
        # Exponential moving average update for global
        self.global_energy = 0.9 * self.global_energy + 0.1 * signal
        return DriftEvent(triggered=False, score=free_energy_diff, threshold=self.threshold, reason="stable")

    def _reset_stats(self):
        self.step_count = 0
        self.history_signal = []
        self.current_window = []
        
    def state_dict(self) -> Dict[str, Any]:
        return {
            "global_energy": self.global_energy,
            "global_entropy": self.global_entropy,
            "step_count": self.step_count,
            "history_signal": self.history_signal,
            "current_window": self.current_window
        }
        
    def load_state_dict(self, state_dict: Dict[str, Any]):
        self.global_energy = state_dict.get("global_energy", 0.0)
        self.global_entropy = state_dict.get("global_entropy", 1.0)
        self.step_count = state_dict.get("step_count", 0)
        self.history_signal = state_dict.get("history_signal", [])
        self.current_window = state_dict.get("current_window", [])
