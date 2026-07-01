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
    A full LoRA integration interface using PEFT.
    """

    def __init__(self, base_model: Any, cfg: LoRAConfig):
        from peft import LoraConfig, get_peft_model
        import torch

        self.base_model = base_model
        self.cfg = cfg
        self._active_adapter_name = "default"
        self._adapters: Dict[str, Dict[str, Any]] = {}

        if self.cfg.enabled:
            # Setup real PEFT model
            peft_config = LoraConfig(
                task_type=getattr(base_model, "peft_task_type", "CAUSAL_LM"),
                inference_mode=False,
                r=self.cfg.r,
                lora_alpha=self.cfg.alpha,
                lora_dropout=self.cfg.dropout,
                target_modules=self.cfg.target_modules
            )
            self.peft_model = get_peft_model(base_model.model, peft_config, adapter_name="default")
            base_model.attach_peft_model(self.peft_model)
            self._adapters["default"] = {"step": 0}
            self._active_adapter_name = "default"
        else:
            self.peft_model = None

    def set_active_adapter(self, name: str) -> None:
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not found. Existing: {list(self._adapters.keys())}")
        self._active_adapter_name = name
        if self.peft_model is not None:
            self.peft_model.set_adapter(name)

    def create_adapter(self, name: str) -> None:
        if name in self._adapters:
            return
        if self.peft_model is not None:
            # Peft supports add_adapter
            from peft import LoraConfig
            peft_config = LoraConfig(
                task_type=getattr(self.base_model, "peft_task_type", "CAUSAL_LM"),
                inference_mode=False,
                r=self.cfg.r,
                lora_alpha=self.cfg.alpha,
                lora_dropout=self.cfg.dropout,
                target_modules=self.cfg.target_modules
            )
            self.peft_model.add_adapter(name, peft_config)
            
            # Since we added new parameters, we need to reset the optimizer in the base model
            if hasattr(self.base_model, "_optimizer"):
                delattr(self.base_model, "_optimizer")

        self._adapters[name] = {"step": 0}

    def list_adapters(self) -> List[str]:
        return list(self._adapters.keys())

    def trainable_parameters(self) -> List[Any]:
        if self.peft_model is not None:
            return [p for p in self.peft_model.parameters() if p.requires_grad]
        return []

    def step_adapter(self) -> None:
        if self._active_adapter_name in self._adapters:
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
