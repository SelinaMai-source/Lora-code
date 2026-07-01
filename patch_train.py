import re

with open("/root/autodl-tmp/Lora-code/core/train.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import
if "SpectralSparseReplayGate" not in content:
    content = content.replace("from core.methods.router import Router", "from core.methods.router import Router\nfrom core.methods.ours_spectral_replay import SpectralSparseReplayGate")

# 2. Add initialization in run_ours
init_str = """
    overlap_cfg = cfg.get("overlap", {}) if isinstance(cfg.get("overlap", {}), dict) else {}
    beta = float(overlap_cfg.get("beta", 0.1))
"""
if "replay_gate =" not in content:
    replay_str = init_str + """
    use_replay = bool(modules.get("use_replay", True))
    replay_cfg = cfg.get("replay", {}) if isinstance(cfg.get("replay", {}), dict) else {}
    replay_gate = SpectralSparseReplayGate(replay_cfg) if use_replay else None
"""
    content = content.replace(init_str, replay_str)

# 3. Add to _train_with_router signature and calls
if "_train_with_router(" in content and "replay_gate: Optional[SpectralSparseReplayGate] = None" not in content:
    content = content.replace("def _train_with_router(\n    *,\n    segment: Segment,\n    model: Any,\n    lora: Any,\n    lora_bank: LoRABank,\n    router: Router,\n    lr: float,\n    epochs: int,\n    batch_size: int,\n)", "def _train_with_router(\n    *,\n    segment: Segment,\n    model: Any,\n    lora: Any,\n    lora_bank: LoRABank,\n    router: Router,\n    lr: float,\n    epochs: int,\n    batch_size: int,\n    replay_gate: Optional[SpectralSparseReplayGate] = None,\n)")
    
    content = content.replace("train_metrics = _train_with_router(\n                segment=seg,\n                model=backbone,\n                lora=lora,\n                lora_bank=lora_bank,\n                router=router,\n                lr=lr,\n                epochs=epochs,\n                batch_size=batch_size,\n            )", "train_metrics = _train_with_router(\n                segment=seg,\n                model=backbone,\n                lora=lora,\n                lora_bank=lora_bank,\n                router=router,\n                lr=lr,\n                epochs=epochs,\n                batch_size=batch_size,\n                replay_gate=replay_gate,\n            )")

# 4. Same for _train_on_active_branch
if "replay_gate: Optional[SpectralSparseReplayGate] = None" not in content.split("def _train_on_active_branch(")[1][:200]:
    content = content.replace("def _train_on_active_branch(*, segment: Segment, model: Any, lora: Any, lr: float, epochs: int, batch_size: int) -> Dict[str, Any]:", "def _train_on_active_branch(*, segment: Segment, model: Any, lora: Any, lr: float, epochs: int, batch_size: int, replay_gate: Optional[SpectralSparseReplayGate] = None) -> Dict[str, Any]:")
    
    content = content.replace("train_metrics = _train_on_active_branch(\n                segment=seg,\n                model=backbone,\n                lora=lora,\n                lr=lr,\n                epochs=epochs,\n                batch_size=batch_size,\n            )", "train_metrics = _train_on_active_branch(\n                segment=seg,\n                model=backbone,\n                lora=lora,\n                lr=lr,\n                epochs=epochs,\n                batch_size=batch_size,\n                replay_gate=replay_gate,\n            )")

# 5. Insert logic into _train_with_router to update and sample
# Before 'for _ in range(max(1, epochs)):'
add_replay_str_router = """
    # Update Replay buffer and mix
    if replay_gate is not None:
        import hashlib
        def get_features(p):
            h = hashlib.sha256(p.encode("utf-8")).digest()
            return [float(b) / 255.0 for b in h]
        features = [get_features(p) for p, _ in pairs]
        replay_gate.update_buffer(segment.segment_id, features, pairs, targets)
        rp_pairs, rp_targets = replay_gate.sample_replay(int(len(pairs) * replay_gate.get_replay_ratio()))
        pairs = pairs + rp_pairs
        targets = targets + rp_targets
        
        # shuffle
        import random
        combined = list(zip(pairs, targets))
        random.shuffle(combined)
        pairs, targets = zip(*combined) if combined else ([], [])
        pairs, targets = list(pairs), list(targets)

    routed = 0
"""
content = re.sub(r'    routed = 0\n\s*batch_accs: List\[float\] = \[\]', add_replay_str_router + '    batch_accs: List[float] = []', content)


add_replay_str_active = """
    if replay_gate is not None:
        import hashlib
        def get_features(p):
            h = hashlib.sha256(p.encode("utf-8")).digest()
            return [float(b) / 255.0 for b in h]
        features = [get_features(p) for p, _ in pairs]
        replay_gate.update_buffer(segment.segment_id, features, pairs, targets)
        rp_pairs, rp_targets = replay_gate.sample_replay(int(len(pairs) * replay_gate.get_replay_ratio()))
        pairs = pairs + rp_pairs
        targets = targets + rp_targets
        import random
        combined = list(zip(pairs, targets))
        random.shuffle(combined)
        pairs, targets = zip(*combined) if combined else ([], [])
        pairs, targets = list(pairs), list(targets)

    batch_accs: List[float] = []
"""
content = re.sub(r'    batch_accs: List\[float\] = \[\]\n\s*batches = 0\n\s*for _ in range\(max\(1, epochs\)\):', add_replay_str_active + '    batches = 0\n    for _ in range(max(1, epochs)):', content, count=1)


with open("/root/autodl-tmp/Lora-code/core/train.py", "w", encoding="utf-8") as f:
    f.write(content)
