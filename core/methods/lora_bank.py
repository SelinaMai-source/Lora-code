from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BranchInfo:
    name: str
    created_at_segment: int
    frozen: bool = False


class LoRABank:
    """
    A lightweight LoRA bank manager.

    Responsibilities:
      - Track branches (adapters) and the active branch
      - Spawn new branches and optionally freeze old ones
      - Enforce max_branches policy (simplified)

    This manager is intentionally model-agnostic. It delegates adapter creation/selection
    to the passed LoRAWrapper.
    """

    def __init__(self, *, max_branches: int = 8):
        self.max_branches = int(max_branches)
        self._branches: Dict[str, BranchInfo] = {}
        self._active: Optional[str] = None
        self._lora_wrapper: Optional[Any] = None

    def initialize(self, *, lora_wrapper: Any, initial_branch: str = "b0", segment_id: int = 0) -> None:
        self._lora_wrapper = lora_wrapper
        if initial_branch not in lora_wrapper.list_adapters():
            lora_wrapper.create_adapter(initial_branch)
        lora_wrapper.set_active_adapter(initial_branch)

        self._branches[initial_branch] = BranchInfo(
            name=initial_branch, created_at_segment=segment_id, frozen=False
        )
        self._active = initial_branch

    def get_active_branch(self) -> str:
        if self._active is None:
            raise RuntimeError("LoRABank not initialized: active branch is None")
        return self._active

    def list_branches(self) -> List[str]:
        return list(self._branches.keys())

    def freeze_current_branch(self) -> None:
        b = self.get_active_branch()
        self._branches[b].frozen = True

    def spawn_new_branch(self, *, lora_wrapper: Any, segment_id: int) -> str:
        """
        Create a new branch and switch to it.
        If max_branches reached, apply a simple policy: do not delete; reuse last branch name with suffix.
        (Future: implement eviction/merge policy.)
        """

        self._lora_wrapper = lora_wrapper
        if len(self._branches) >= self.max_branches:
            # simple deterministic reuse naming to avoid destructive deletes
            name = f"b{len(self._branches)}_overflow_s{segment_id}"
        else:
            name = f"b{len(self._branches)}"

        if name not in lora_wrapper.list_adapters():
            lora_wrapper.create_adapter(name)
        lora_wrapper.set_active_adapter(name)

        self._branches[name] = BranchInfo(name=name, created_at_segment=segment_id, frozen=False)
        self._active = name
        return name

    def set_active_adapter(self, name: str) -> None:
        """
        Switch the underlying PEFT adapter if the bank is backed by a LoRAWrapper.
        This is needed for evaluation-time routing where we may choose a branch
        per prompt and then generate with the selected adapter.
        """
        if self._lora_wrapper is None:
            raise RuntimeError("LoRABank has no lora_wrapper reference; initialize/spawn must be called first.")
        self._lora_wrapper.set_active_adapter(name)

    def state_dict(self) -> Dict[str, Any]:
        return {
            "max_branches": self.max_branches,
            "active": self._active,
            "branches": {k: vars(v) for k, v in self._branches.items()},
        }

