from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LoRAConfig:
    enabled: bool = True
    r: int = 16
    alpha: int = 32
    dropout: float = 0.0
    target_modules: Optional[List[str]] = None


class LoRAWrapper:
    """
    A minimal LoRA integration interface.

    Current simplified path (debug):
      - We do NOT patch real transformer layers.
      - We keep a small per-branch adapter "state" and expose a stable API.

    Future full path (HF/PEFT):
      - Replace internal logic with PEFT's `get_peft_model(...)`
      - `trainable_parameters()` should return actual torch parameters
      - `save_adapter(...)` / `load_adapter(...)` can map to PEFT checkpoints
    """

    def __init__(self, base_model: Any, cfg: LoRAConfig):
        self.base_model = base_model
        self.cfg = cfg
        self._active_adapter_name = "default"
        self._adapters: Dict[str, Dict[str, Any]] = {"default": {"step": 0}}

    def set_active_adapter(self, name: str) -> None:
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not found. Existing: {list(self._adapters.keys())}")
        self._active_adapter_name = name

    def create_adapter(self, name: str) -> None:
        if name in self._adapters:
            raise KeyError(f"Adapter '{name}' already exists.")
        self._adapters[name] = {"step": 0}

    def list_adapters(self) -> List[str]:
        return list(self._adapters.keys())

    def trainable_parameters(self) -> List[Any]:
        # Debug model has no torch parameters; return empty.
        # HF+PEFT path should return a list of torch.nn.Parameter.
        return []

    def step_adapter(self) -> None:
        self._adapters[self._active_adapter_name]["step"] += 1

    def get_active_adapter_name(self) -> str:
        return self._active_adapter_name

    def info(self) -> Dict[str, Any]:
        return {
            "enabled": self.cfg.enabled,
            "r": self.cfg.r,
            "alpha": self.cfg.alpha,
            "dropout": self.cfg.dropout,
            "target_modules": self.cfg.target_modules or [],
            "active_adapter": self._active_adapter_name,
            "adapters": {k: dict(v) for k, v in self._adapters.items()},
        }


def build_lora_wrapper(base_model: Any, lora_cfg_dict: Dict[str, Any]) -> LoRAWrapper:
    cfg = LoRAConfig(
        enabled=bool(lora_cfg_dict.get("enabled", True)),
        r=int(lora_cfg_dict.get("r", 16)),
        alpha=int(lora_cfg_dict.get("alpha", 32)),
        dropout=float(lora_cfg_dict.get("dropout", 0.0)),
        target_modules=list(lora_cfg_dict.get("target_modules", [])) or None,
    )
    return LoRAWrapper(base_model=base_model, cfg=cfg)

