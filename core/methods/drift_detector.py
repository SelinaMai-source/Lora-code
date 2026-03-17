from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DriftEvent:
    triggered: bool
    score: float
    threshold: float
    reason: str


class DriftDetector:
    """
    A modular drift detector (simplified but real stateful logic).

    Intended mapping to research prototype (RP):
      - Maintain a rolling estimate of "distribution shift" between the current segment
        and a calibration window of recent segments.
      - In full implementation, score could come from anchor/probe prompts, gradient stats,
        activation distance, or router uncertainty.

    Current simplified implementation:
      - Uses an exponential moving average (EMA) of per-segment "difficulty delta".
      - The pipeline feeds a scalar signal each segment via `update(signal=...)`.
      - Triggers drift when EMA exceeds a threshold.
    """

    def __init__(self, cfg: Dict[str, Any]):
        self.anchor_size = int(cfg.get("anchor_size", 64))
        self.monitor_interval = int(cfg.get("monitor_interval", 50))
        self.calibration_window = int(cfg.get("calibration_window", 200))
        self.threshold = float(cfg.get("threshold", 0.15))
        self.score_ema = float(cfg.get("score_ema", 0.9))

        self._ema: Optional[float] = None
        self._num_updates = 0
        self._history: List[float] = []

    def reset(self) -> None:
        self._ema = None
        self._num_updates = 0
        self._history = []

    def update(self, *, signal: float, segment_id: int) -> DriftEvent:
        """
        Update detector state with a scalar signal for this segment.

        signal meaning (recommended):
          - 1 - current_segment_accuracy (higher means harder / more shift)
          - or any normalized drift proxy in [0, 1]
        """

        self._num_updates += 1
        self._history.append(float(signal))
        if self._ema is None:
            self._ema = float(signal)
        else:
            self._ema = self.score_ema * self._ema + (1.0 - self.score_ema) * float(signal)

        score = float(self._ema)
        triggered = score >= self.threshold
        reason = f"ema_signal={score:.4f} >= threshold={self.threshold:.4f}" if triggered else "below_threshold"

        return DriftEvent(triggered=triggered, score=score, threshold=self.threshold, reason=reason)

    def state_dict(self) -> Dict[str, Any]:
        return {
            "ema": self._ema,
            "num_updates": self._num_updates,
            "history_tail": self._history[-50:],
            "threshold": self.threshold,
        }

