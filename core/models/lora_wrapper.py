from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch

from peft import LoraConfig as PeftLoraConfig
from peft import TaskType
from peft import get_peft_model


@dataclass
class LoRAConfig:
    enabled: bool = True
    r: int = 16
    alpha: int = 32
    dropout: float = 0.0
    # PEFT accepts a list of module names or strings like "all-linear".
    target_modules: Optional[Union[str, List[str]]] = None


class LoRAWrapper:
    """
    Real PEFT LoRA wrapper with multiple adapters.

    This wrapper integrates with the repo's unified training loop:
      - `backbone.fit_batch(...)` computes loss and calls `loss.backward()`
      - `LoRAWrapper.step_adapter()` performs optimizer.step() + zero_grad()
    """

    def __init__(self, backbone: Any, cfg: LoRAConfig):
        """
        backbone: `core/models/base_model.py` backbone object.
                 Must implement:
                   - attach_peft_model(peft_model)
                   - attribute `_last_lr` updated by fit_batch(...)
        """
        self.backbone = backbone
        self.cfg = cfg
        self._active_adapter_name: str = "default"
        self._adapter_steps: Dict[str, int] = {"default": 0}

        if not self.cfg.enabled:
            # Still create a wrapper so downstream code doesn't crash, but do not add adapters.
            self.peft_model = None
            self._optimizer = None
            return

        tm = self.cfg.target_modules
        if tm is None or (isinstance(tm, list) and len(tm) == 0) or (isinstance(tm, str) and not tm.strip()):
            raise ValueError("LoRA enabled but `target_modules` is empty.")

        peft_modules: Any = tm if isinstance(tm, str) else list(tm)

        peft_cfg = PeftLoraConfig(
            r=int(self.cfg.r),
            lora_alpha=int(self.cfg.alpha),
            lora_dropout=float(self.cfg.dropout),
            bias="none",
            target_modules=peft_modules,
            task_type=TaskType.CAUSAL_LM,
        )

        # Create default adapter and attach PEFT model to backbone.
        self.peft_model = get_peft_model(self.backbone.model, peft_cfg, adapter_name="default")
        self.backbone.attach_peft_model(self.peft_model)

        # Set only the default adapter as trainable initially.
        self.set_active_adapter("default")
        self._optimizer = None
        self._rebuild_optimizer()

    def set_active_adapter(self, name: str) -> None:
        if not self.cfg.enabled:
            self._active_adapter_name = name
            return

        adapters = set(self.list_adapters())
        if name not in adapters:
            raise KeyError(f"Adapter '{name}' not found. Existing: {sorted(list(adapters))}")

        self._active_adapter_name = name
        if self.peft_model is not None:
            self.peft_model.set_adapter(name)

            # Train only the active adapter's LoRA parameters.
            # PEFT parameter names typically include: "...lora_A.<adapter_name>..." / "...lora_B.<adapter_name>..."
            for param_name, param in self.peft_model.named_parameters():
                if "lora_" in param_name:
                    param.requires_grad = (name in param_name)
                else:
                    param.requires_grad = False

        # optimizer param groups already contain LoRA params; no need to rebuild here

    def save_adapter_checkpoint(self, path: str) -> None:
        """Write PEFT adapter to a directory (e.g. for overfit resume / latest snapshot)."""
        if not self.cfg.enabled or self.peft_model is None:
            return
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        self.peft_model.save_pretrained(str(p))

    def load_adapter_checkpoint(self, path: str) -> None:
        """Load adapter weights into the active adapter; rebuilds optimizer (Adam state reset)."""
        if not self.cfg.enabled or self.peft_model is None:
            return
        p = Path(path)
        if not p.is_dir():
            raise FileNotFoundError(f"Adapter checkpoint not found: {p}")
        self.peft_model.load_adapter(
            str(p.resolve()), adapter_name=self._active_adapter_name, is_trainable=True
        )
        self.set_active_adapter(self._active_adapter_name)
        self._rebuild_optimizer()

    def create_adapter(self, name: str) -> None:
        if not self.cfg.enabled:
            self._adapter_steps[name] = 0
            self._active_adapter_name = name
            return

        adapters = set(self.list_adapters())
        if name in adapters:
            raise KeyError(f"Adapter '{name}' already exists.")

        tm = self.cfg.target_modules
        peft_modules_add: Any = tm if isinstance(tm, str) else list(tm or [])

        peft_cfg = PeftLoraConfig(
            r=int(self.cfg.r),
            lora_alpha=int(self.cfg.alpha),
            lora_dropout=float(self.cfg.dropout),
            bias="none",
            target_modules=peft_modules_add,
            task_type=TaskType.CAUSAL_LM,
        )
        self.peft_model.add_adapter(adapter_name=name, peft_config=peft_cfg)
        self._adapter_steps[name] = 0

        # New adapter adds new parameters, so rebuild optimizer param groups.
        self._rebuild_optimizer()

    def list_adapters(self) -> List[str]:
        if not self.cfg.enabled or self.peft_model is None:
            return list(self._adapter_steps.keys())
        # `peft_model.peft_config` is a dict: adapter_name -> config
        try:
            return list(self.peft_model.peft_config.keys())
        except Exception:
            return list(self._adapter_steps.keys())

    def trainable_parameters(self) -> List[Any]:
        if not self.cfg.enabled or self.peft_model is None:
            return []
        return [p for p in self.peft_model.parameters() if p.requires_grad]

    def step_adapter(self) -> Dict[str, Any]:
        if not self.cfg.enabled or self.peft_model is None or self._optimizer is None:
            self._adapter_steps[self._active_adapter_name] = self._adapter_steps.get(self._active_adapter_name, 0) + 1
            return {
                "grad_norm": 0.0,
                "lora_param_delta_l2": 0.0,
                "lora_params_changed": False,
                "lr": float(getattr(self.backbone, "_last_lr", 0.0) or 0.0),
            }

        # Update LR from backbone's last fit_batch(...)
        lr = float(getattr(self.backbone, "_last_lr", 0.0) or 0.0)
        if lr > 0:
            for group in self._optimizer.param_groups:
                group["lr"] = lr

        lora_named_params = [(n, p) for n, p in self.peft_model.named_parameters() if "lora_" in n and p.requires_grad]
        grad_sq_sum = 0.0
        before = []
        with torch.no_grad():
            for _, p in lora_named_params:
                if p.grad is not None:
                    grad_sq_sum += float((p.grad.detach().float() ** 2).sum().item())
                before.append(p.detach().clone())
        grad_norm = float(grad_sq_sum ** 0.5)

        self._optimizer.step()
        self._optimizer.zero_grad(set_to_none=True)

        delta_sq_sum = 0.0
        with torch.no_grad():
            for (_, p), b in zip(lora_named_params, before):
                delta = p.detach().float() - b.float()
                delta_sq_sum += float((delta ** 2).sum().item())
        delta_norm = float(delta_sq_sum ** 0.5)

        self._adapter_steps[self._active_adapter_name] = self._adapter_steps.get(self._active_adapter_name, 0) + 1
        return {
            "grad_norm": grad_norm,
            "lora_param_delta_l2": delta_norm,
            "lora_params_changed": bool(delta_norm > 0.0),
            "lr": float(lr),
        }

    def get_active_adapter_name(self) -> str:
        return self._active_adapter_name

    def info(self) -> Dict[str, Any]:
        total_params = 0
        trainable_params = 0
        trainable_names: List[str] = []
        if self.peft_model is not None:
            for n, p in self.peft_model.named_parameters():
                n_params = int(p.numel())
                total_params += n_params
                if p.requires_grad:
                    trainable_params += n_params
                    trainable_names.append(n)
        tm = self.cfg.target_modules
        tm_out: Any = tm if isinstance(tm, str) else (tm or [])
        return {
            "enabled": self.cfg.enabled,
            "r": self.cfg.r,
            "alpha": self.cfg.alpha,
            "dropout": self.cfg.dropout,
            "target_modules": tm_out,
            "active_adapter": self._active_adapter_name,
            "adapters": dict(self._adapter_steps),
            "total_parameters": int(total_params),
            "trainable_parameters": int(trainable_params),
            "trainable_parameter_names": trainable_names,
        }

    def _rebuild_optimizer(self) -> None:
        if not self.cfg.enabled or self.peft_model is None:
            self._optimizer = None
            return

        # Include all LoRA parameters of all adapters currently registered.
        lora_params = [p for n, p in self.peft_model.named_parameters() if "lora_" in n]
        if not lora_params:
            self._optimizer = None
            return

        # AdamW is a common default; training hyperparameters are controlled via `lr` passed to fit_batch.
        self._optimizer = torch.optim.AdamW(lora_params, lr=1e-4)


class DebugLoRAWrapper:
    """
    Debug/no-op LoRA wrapper used when the backbone is the repo's DebugTextModel.

    It keeps the adapter-selection API stable so the rest of the pipeline can run.
    """

    def __init__(self, cfg: LoRAConfig):
        self.cfg = cfg
        self._active_adapter_name: str = "default"
        self._adapter_steps: Dict[str, int] = {"default": 0}

    def set_active_adapter(self, name: str) -> None:
        if name not in self._adapter_steps:
            raise KeyError(f"Adapter '{name}' not found. Existing: {sorted(list(self._adapter_steps.keys()))}")
        self._active_adapter_name = name

    def create_adapter(self, name: str) -> None:
        if name in self._adapter_steps:
            raise KeyError(f"Adapter '{name}' already exists.")
        self._adapter_steps[name] = 0

    def list_adapters(self) -> List[str]:
        return list(self._adapter_steps.keys())

    def trainable_parameters(self) -> List[Any]:
        return []

    def step_adapter(self) -> Dict[str, Any]:
        self._adapter_steps[self._active_adapter_name] = self._adapter_steps.get(self._active_adapter_name, 0) + 1
        return {
            "grad_norm": 0.0,
            "lora_param_delta_l2": 0.0,
            "lora_params_changed": False,
            "lr": 0.0,
        }

    def get_active_adapter_name(self) -> str:
        return self._active_adapter_name

    def save_adapter_checkpoint(self, path: str) -> None:
        return

    def load_adapter_checkpoint(self, path: str) -> None:
        return

    def info(self) -> Dict[str, Any]:
        tm = self.cfg.target_modules
        tm_out: Any = tm if isinstance(tm, str) else (tm or [])
        return {
            "enabled": self.cfg.enabled,
            "r": self.cfg.r,
            "alpha": self.cfg.alpha,
            "dropout": self.cfg.dropout,
            "target_modules": tm_out,
            "active_adapter": self._active_adapter_name,
            "adapters": dict(self._adapter_steps),
        }


def build_lora_wrapper(base_model: Any, lora_cfg_dict: Dict[str, Any]) -> LoRAWrapper:
    raw_tm = lora_cfg_dict.get("target_modules", [])
    if isinstance(raw_tm, str):
        parsed_tm: Optional[Union[str, List[str]]] = raw_tm.strip()
    else:
        lst = list(raw_tm or [])
        parsed_tm = lst if lst else None

    cfg = LoRAConfig(
        enabled=bool(lora_cfg_dict.get("enabled", True)),
        r=int(lora_cfg_dict.get("r", 16)),
        alpha=int(lora_cfg_dict.get("alpha", 32)),
        dropout=float(lora_cfg_dict.get("dropout", 0.0)),
        target_modules=parsed_tm,
    )
    # Debug backbones (DebugTextModel) don't have PEFT hooks.
    if not hasattr(base_model, "attach_peft_model") or not hasattr(base_model, "model"):
        return DebugLoRAWrapper(cfg=cfg)  # type: ignore[return-value]

    return LoRAWrapper(backbone=base_model, cfg=cfg)

