from __future__ import annotations

import sys
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow running as: `python core/train.py --config ...` without requiring package installs.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data import ContinualStream, Segment, load_continual_stream
from core.evaluate import evaluate_stream
from core.methods.drift_detector import DriftDetector
from core.methods.lora_bank import LoRABank
from core.methods.overlap_loss import compute_overlap_loss
from core.methods.router import Router
from core.methods.ours_spectral_replay import SpectralSparseReplayGate
from core.models.base_model import build_backbone
from core.models.lora_wrapper import build_lora_wrapper
from core.utils import RunPaths, SimpleLogger, ensure_dir, load_yaml_config, make_run_paths, save_json, save_csv, set_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified continual instruction tuning pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    mode = str(cfg.get("mode", "")).strip()
    if mode not in {"debug", "baseline", "ours"}:
        raise ValueError(f"Invalid mode={mode}. Expected one of: debug | baseline | ours")

    seed = int(cfg.get("seed", 0))
    set_seed(seed)

    results_dir = str(cfg.get("paths", {}).get("results_dir", "results"))
    experiment_name = str(cfg.get("experiment_name", "experiment"))
    run_name = str(cfg.get("output", {}).get("run_name", "")) if isinstance(cfg.get("output", {}), dict) else ""
    run_paths = make_run_paths(results_dir=results_dir, experiment_name=experiment_name, run_name=run_name)
    logger = SimpleLogger(run_paths.log_file)

    logger.log(f"Config: {args.config}")
    logger.log(f"Mode: {mode}")
    logger.log(f"Run ID: {run_paths.run_id}")

    # Snapshot config for reproducibility
    save_json(str(Path(run_paths.run_dir) / "config_snapshot.json"), cfg)

    stream = _load_stream(cfg, mode=mode, logger=logger)
    logger.log(f"Loaded stream: benchmark={stream.benchmark} version={stream.version} segments={len(stream.stream)}")

    debug_loading = str(cfg.get("debug", {}).get("model_loading", "dummy")) if isinstance(cfg.get("debug", {}), dict) else "dummy"
    backbone = build_backbone(cfg.get("model", {}), mode=mode, seed=seed, debug_loading=debug_loading)
    lora = build_lora_wrapper(backbone, cfg.get("lora", {}))
    logger.log(f"LoRA: {json.dumps(lora.info(), ensure_ascii=False)}")

    segment_metrics_rows: List[Dict[str, Any]] = []

    if mode == "debug":
        baseline_name = str(cfg.get("baseline", {}).get("baseline_name", "sequential_lora"))
        final_metrics = run_baseline(
            cfg=cfg,
            stream=stream,
            backbone=backbone,
            lora=lora,
            baseline_name=baseline_name,
            run_paths=run_paths,
            logger=logger,
            segment_metrics_rows=segment_metrics_rows,
            mode="debug",
        )
    elif mode == "baseline":
        baseline_name = str(cfg.get("baseline_name", "")).strip()
        if not baseline_name:
            raise ValueError("baseline mode requires config field: baseline_name")
        final_metrics = run_baseline(
            cfg=cfg,
            stream=stream,
            backbone=backbone,
            lora=lora,
            baseline_name=baseline_name,
            run_paths=run_paths,
            logger=logger,
            segment_metrics_rows=segment_metrics_rows,
            mode="baseline",
        )
    else:
        final_metrics = run_ours(
            cfg=cfg,
            stream=stream,
            backbone=backbone,
            lora=lora,
            run_paths=run_paths,
            logger=logger,
            segment_metrics_rows=segment_metrics_rows,
        )

    # Save final metrics + per-segment table
    save_json(run_paths.metrics_json, final_metrics)
    save_csv(run_paths.segment_metrics_csv, segment_metrics_rows)
    logger.log(f"Saved final metrics: {run_paths.metrics_json}")
    logger.log(f"Saved per-segment table: {run_paths.segment_metrics_csv}")


def _load_stream(cfg: Dict[str, Any], *, mode: str, logger: SimpleLogger) -> ContinualStream:
    paths = cfg.get("paths", {}) if isinstance(cfg.get("paths", {}), dict) else {}
    sample_stream_path = paths.get("sample_stream_path")
    processed_dir = paths.get("processed_stream_dir")
    processed_file = str(paths.get("processed_stream_file", "")).strip()

    if mode == "debug":
        dbg = cfg.get("debug", {}) if isinstance(cfg.get("debug", {}), dict) else {}
        max_segments = int(dbg.get("max_segments", -1))
        max_train = int(dbg.get("max_train_examples_per_segment", -1))
        max_eval = int(dbg.get("max_eval_examples_per_segment", -1))
        return load_continual_stream(
            mode="debug",
            sample_stream_path=str(sample_stream_path),
            processed_stream_dir=None,
            processed_stream_file="",
            max_segments=max_segments,
            max_train_examples_per_segment=max_train,
            max_eval_examples_per_segment=max_eval,
        )

    data_cfg = cfg.get("data", {}) if isinstance(cfg.get("data", {}), dict) else {}
    max_segments = int(data_cfg.get("max_segments", -1))
    max_train = int(data_cfg.get("max_train_examples_per_segment", -1))
    max_eval = int(data_cfg.get("max_eval_examples_per_segment", -1))

    if processed_dir is None:
        raise ValueError("processed_stream_dir is required for baseline/ours modes")

    return load_continual_stream(
        mode=mode,
        sample_stream_path=None,
        processed_stream_dir=str(processed_dir),
        processed_stream_file=processed_file,
        max_segments=max_segments,
        max_train_examples_per_segment=max_train,
        max_eval_examples_per_segment=max_eval,
    )


def run_baseline(
    *,
    cfg: Dict[str, Any],
    stream: ContinualStream,
    backbone: Any,
    lora: Any,
    baseline_name: str,
    run_paths: RunPaths,
    logger: SimpleLogger,
    segment_metrics_rows: List[Dict[str, Any]],
    mode: str,
) -> Dict[str, Any]:
    logger.log(f"Baseline selected: {baseline_name}")

    train_cfg = cfg.get("train", {}) if isinstance(cfg.get("train", {}), dict) else {}
    lr = float(train_cfg.get("lr", 1e-3))
    epochs = int(train_cfg.get("epochs_per_segment", 1))
    batch_size = int(train_cfg.get("batch_size", 1))

    # Optional shared components (used by some baselines)
    lora_bank = LoRABank(max_branches=int(cfg.get("periodic", {}).get("max_branches", 8)) if isinstance(cfg.get("periodic", {}), dict) else 8)
    router = Router(cfg.get("router", {}) if isinstance(cfg.get("router", {}), dict) else {})
    drift = DriftDetector(cfg.get("drift", {}) if isinstance(cfg.get("drift", {}), dict) else {})

    method = _build_baseline_method(baseline_name, cfg)

    seen_segments: List[Segment] = []
    for seg in stream.stream:
        logger.log(f"=== Segment {seg.segment_id}: {seg.segment_name} ===")

        hook_info = {}
        if hasattr(method, "on_segment_start"):
            hook_info = method.on_segment_start(segment=seg, model=backbone, lora=lora)

        # Train
        if baseline_name == "router_only":
            train_metrics = method.train_on_segment(
                segment=seg,
                model=backbone,
                lora=lora,
                router=router,
                lora_bank=lora_bank,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
            )
        elif baseline_name == "bank_no_router":
            train_metrics = _train_bank_no_router(
                segment=seg,
                model=backbone,
                lora=lora,
                lora_bank=lora_bank,
                drift=drift,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
            )
        else:
            train_metrics = method.train_on_segment(
                segment=seg, model=backbone, lora=lora, lr=lr, epochs=epochs, batch_size=batch_size
            )

        logger.log(f"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}")

        # Update router prototypes using all training prompts for the current active branch
        if router is not None:
            all_prompts = [_format_prompt(ex.instruction, ex.input) for ex in seg.train]
            active_b = lora.get_active_adapter_name()
            # Feed current branch as the pseudo label
            router.update_with_pseudo_labels(
                batch_prompts=all_prompts,
                pseudo_labels=[active_b] * len(all_prompts),
                branch_names=[active_b]
            )
            logger.log(f"Updated router prototypes for branch {active_b} with {len(all_prompts)} examples.")


        # Evaluate on seen segments (unified)
        seen_segments.append(seg)
        eval_metrics = evaluate_stream(
            model=backbone,
            segments_seen=seen_segments,
            router=router if baseline_name == "router_only" else None,
            lora_bank=lora_bank if baseline_name == "router_only" else None,
            segment_id=seg.segment_id,
        )
        logger.log(f"Eval metrics: {json.dumps(eval_metrics, ensure_ascii=False)}")

        row = {
            "run_id": run_paths.run_id,
            "mode": mode,
            "baseline_name": baseline_name,
            "segment_id": seg.segment_id,
            "segment_name": seg.segment_name,
            **_flatten_metrics("train", train_metrics),
            **_flatten_metrics("eval", eval_metrics),
            **{f"hook.{k}": v for k, v in (hook_info or {}).items()},
            "active_adapter": lora.get_active_adapter_name(),
        }
        segment_metrics_rows.append(row)

        # Save per-segment artifact
        seg_dir = ensure_dir(str(Path(run_paths.run_dir) / f"segment_{seg.segment_id:03d}"))
        save_json(str(Path(seg_dir) / "train_metrics.json"), train_metrics)
        save_json(str(Path(seg_dir) / "eval_metrics.json"), eval_metrics)

    final = segment_metrics_rows[-1] if segment_metrics_rows else {}
    return {
        "run_id": run_paths.run_id,
        "mode": mode,
        "baseline_name": baseline_name,
        "final": final,
    }


def run_ours(
    *,
    cfg: Dict[str, Any],
    stream: ContinualStream,
    backbone: Any,
    lora: Any,
    run_paths: RunPaths,
    logger: SimpleLogger,
    segment_metrics_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    modules = cfg.get("modules", {}) if isinstance(cfg.get("modules", {}), dict) else {}
    use_drift = bool(modules.get("use_drift_detector", True))
    use_bank = bool(modules.get("use_lora_bank", True))
    use_router = bool(modules.get("use_router", True))
    use_overlap = bool(modules.get("use_overlap_loss", True))

    logger.log(
        "Ours modules: "
        + json.dumps(
            {
                "use_drift_detector": use_drift,
                "use_lora_bank": use_bank,
                "use_router": use_router,
                "use_overlap_loss": use_overlap,
            },
            ensure_ascii=False,
        )
    )

    train_cfg = cfg.get("train", {}) if isinstance(cfg.get("train", {}), dict) else {}
    lr = float(train_cfg.get("lr", 1e-4))
    epochs = int(train_cfg.get("epochs_per_segment", 1))
    batch_size = int(train_cfg.get("batch_size", 1))

    drift = DriftDetector(cfg.get("drift", {}) if isinstance(cfg.get("drift", {}), dict) else {}) if use_drift else None
    bank_cfg = cfg.get("bank", {}) if isinstance(cfg.get("bank", {}), dict) else {}
    lora_bank = LoRABank(max_branches=int(bank_cfg.get("max_branches", 8))) if use_bank else None
    router = Router(cfg.get("router", {}) if isinstance(cfg.get("router", {}), dict) else {}) if use_router else None
    overlap_cfg = cfg.get("overlap", {}) if isinstance(cfg.get("overlap", {}), dict) else {}
    beta = float(overlap_cfg.get("beta", 0.1))

    use_replay = bool(modules.get("use_replay", True))
    replay_cfg = cfg.get("replay", {}) if isinstance(cfg.get("replay", {}), dict) else {}
    replay_gate = SpectralSparseReplayGate(replay_cfg) if use_replay else None

    # Initialize bank with first branch if enabled
    if lora_bank is not None:
        lora_bank.initialize(lora_wrapper=lora, initial_branch="b0", segment_id=0)

    seen_segments: List[Segment] = []
    for seg in stream.stream:
        logger.log(f"=== Segment {seg.segment_id}: {seg.segment_name} ===")

        # Decide which branch to use for training
        if lora_bank is not None and router is not None:
            # Route per example (hard routing); switch adapter before fit
            train_metrics = _train_with_router(
                segment=seg,
                model=backbone,
                lora=lora,
                lora_bank=lora_bank,
                router=router,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
                replay_gate=replay_gate,
            )
        elif lora_bank is not None and router is None:
            # No router: always use the active branch
            train_metrics = _train_on_active_branch(
                segment=seg,
                model=backbone,
                lora=lora,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
                replay_gate=replay_gate,
            )
        else:
            # No bank: fall back to single default adapter
            if "default" in lora.list_adapters():
                lora.set_active_adapter("default")
            train_metrics = _train_on_active_branch(
                segment=seg,
                model=backbone,
                lora=lora,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
                replay_gate=replay_gate,
            )

        # Optional overlap loss (logged as a scalar proxy)
        overlap_value = 0.0
        if use_overlap and lora_bank is not None:
            anchor_prompts = [_format_prompt(ex.instruction, ex.input) for ex in seg.eval[:8]]
            activations_by_branch: Dict[str, List[List[float]]] = {}
            for b in lora_bank.list_branches():
                lora.set_active_adapter(b)
                activations_by_branch[b] = backbone.get_activations(anchor_prompts)
            overlap_value = compute_overlap_loss(activations_by_branch=activations_by_branch, beta=beta)
            train_metrics["overlap_loss_proxy"] = float(overlap_value)

        logger.log(f"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}")

        # Update router prototypes using all training prompts for the current active branch
        if router is not None:
            all_prompts = [_format_prompt(ex.instruction, ex.input) for ex in seg.train]
            active_b = lora.get_active_adapter_name()
            # Feed current branch as the pseudo label
            router.update_with_pseudo_labels(
                batch_prompts=all_prompts,
                pseudo_labels=[active_b] * len(all_prompts),
                branch_names=[active_b]
            )
            logger.log(f"Updated router prototypes for branch {active_b} with {len(all_prompts)} examples.")


        # Evaluate
        seen_segments.append(seg)
        eval_metrics = evaluate_stream(
            model=backbone,
            segments_seen=seen_segments,
            router=router if (router is not None and lora_bank is not None) else None,
            lora_bank=lora_bank if (router is not None and lora_bank is not None) else None,
            segment_id=seg.segment_id,
        )
        logger.log(f"Eval metrics: {json.dumps(eval_metrics, ensure_ascii=False)}")

        # Drift update after seeing eval results (simple proxy)
        drift_event = None
        if drift is not None:
            signal = 1.0 - float(eval_metrics.get("current_score", 0.0))
            drift_event = drift.update(signal=signal, segment_id=seg.segment_id)
            logger.log(
                f"Drift detector: triggered={drift_event.triggered} score={drift_event.score:.4f} "
                f"threshold={drift_event.threshold:.4f} reason={drift_event.reason}"
            )

        # Spawn branch on drift (if enabled)
        if lora_bank is not None and drift_event is not None:
            if bool(bank_cfg.get("spawn_on_drift", True)) and drift_event.triggered:
                if bool(bank_cfg.get("freeze_old_branches", True)):
                    lora_bank.freeze_current_branch()
                new_b = lora_bank.spawn_new_branch(lora_wrapper=lora, segment_id=seg.segment_id)
                logger.log(f"Spawned new branch due to drift: {new_b}")

        row = {
            "run_id": run_paths.run_id,
            "mode": "ours",
            "segment_id": seg.segment_id,
            "segment_name": seg.segment_name,
            **_flatten_metrics("train", train_metrics),
            **_flatten_metrics("eval", eval_metrics),
            "active_adapter": lora.get_active_adapter_name(),
            "overlap_loss_proxy": float(overlap_value),
            "num_branches": len(lora_bank.list_branches()) if lora_bank is not None else 1,
        }
        if drift_event is not None:
            row["drift.triggered"] = bool(drift_event.triggered)
            row["drift.score"] = float(drift_event.score)
        segment_metrics_rows.append(row)

        seg_dir = ensure_dir(str(Path(run_paths.run_dir) / f"segment_{seg.segment_id:03d}"))
        save_json(str(Path(seg_dir) / "train_metrics.json"), train_metrics)
        save_json(str(Path(seg_dir) / "eval_metrics.json"), eval_metrics)
        if drift is not None:
            save_json(str(Path(seg_dir) / "drift_state.json"), drift.state_dict())
        if lora_bank is not None:
            save_json(str(Path(seg_dir) / "bank_state.json"), lora_bank.state_dict())
        if router is not None:
            save_json(str(Path(seg_dir) / "router_state.json"), router.state_dict())

    final = segment_metrics_rows[-1] if segment_metrics_rows else {}
    return {"run_id": run_paths.run_id, "mode": "ours", "final": final}


def _build_baseline_method(baseline_name: str, cfg: Dict[str, Any]) -> Any:
    if baseline_name == "sequential_lora":
        from baselines.sequential_lora.method import SequentialLoRAMethod

        return SequentialLoRAMethod(cfg)
    if baseline_name == "replay_lora":
        from baselines.replay_lora.method import ReplayLoRAMethod

        return ReplayLoRAMethod(cfg)
    if baseline_name == "periodic_multilora":
        from baselines.periodic_multilora.method import PeriodicMultiLoRAMethod

        return PeriodicMultiLoRAMethod(cfg)
    if baseline_name == "router_only":
        from baselines.router_only.method import RouterOnlyMethod

        return RouterOnlyMethod(cfg)
    if baseline_name == "bank_no_router":
        # Implemented directly in core/train.py to avoid creating a new baseline folder.
        return object()
    raise ValueError(
        "Unknown baseline_name. Expected one of: "
        "sequential_lora | replay_lora | periodic_multilora | router_only | bank_no_router"
    )


def _train_on_active_branch(*, segment: Segment, model: Any, lora: Any, lr: float, epochs: int, batch_size: int, replay_gate: Optional[SpectralSparseReplayGate] = None) -> Dict[str, Any]:
    from baselines.sequential_lora.method import _batch, _format_prompt

    pairs = [(_format_prompt(ex.instruction, ex.input), ex.input) for ex in segment.train]
    targets = [ex.output for ex in segment.train]


    if replay_gate is not None:
        import hashlib

        def get_features(p):
            vec = [0.0] * 256
            p_text = p[:200].lower()
            if len(p_text) < 3: p_text = p_text.ljust(3, ' ')
            for i in range(len(p_text) - 2):
                tri = p_text[i:i+3]
                idx = sum(ord(c)*(31**j) for j,c in enumerate(tri)) % 256
                vec[idx] += 1.0
            return vec

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
    batches = 0
    for _ in range(max(1, epochs)):
        for b_pairs, b_targets in _batch(pairs, targets, batch_size):
            out = model.fit_batch(b_pairs, b_targets, lr=lr)
            lora.step_adapter()
            batch_accs.append(float(out.get("train_batch_acc", 0.0)))
            batches += 1
    return {"batches": batches, "mean_batch_acc": sum(batch_accs) / max(1, len(batch_accs))}


def _train_with_router(
    *,
    segment: Segment,
    model: Any,
    lora: Any,
    lora_bank: LoRABank,
    router: Router,
    lr: float,
    epochs: int,
    batch_size: int,
    replay_gate: Optional[SpectralSparseReplayGate] = None,
) -> Dict[str, Any]:
    from baselines.sequential_lora.method import _batch, _format_prompt

    pairs = [(_format_prompt(ex.instruction, ex.input), ex.input) for ex in segment.train]
    targets = [ex.output for ex in segment.train]


    # Update Replay buffer and mix
    if replay_gate is not None:
        import hashlib

        def get_features(p):
            vec = [0.0] * 256
            p_text = p[:200].lower()
            if len(p_text) < 3: p_text = p_text.ljust(3, ' ')
            for i in range(len(p_text) - 2):
                tri = p_text[i:i+3]
                idx = sum(ord(c)*(31**j) for j,c in enumerate(tri)) % 256
                vec[idx] += 1.0
            return vec

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
    batch_accs: List[float] = []
    batches = 0
    for _ in range(max(1, epochs)):
        for b_pairs, b_targets in _batch(pairs, targets, batch_size):
            for (prompt, _), y in zip(b_pairs, b_targets):
                decision = router.predict_branch(
                    prompt=prompt,
                    branch_names=lora_bank.list_branches(),
                    branch_meta=lora_bank.state_dict(),
                    segment_id=segment.segment_id,
                )
                lora.set_active_adapter(decision.branch_name)
                out = model.fit_batch([(prompt, "")], [y], lr=lr)
                lora.step_adapter()
                routed += 1
                batch_accs.append(float(out.get("train_batch_acc", 0.0)))
            batches += 1
    return {
        "batches": batches,
        "mean_batch_acc": sum(batch_accs) / max(1, len(batch_accs)),
        "routed_examples": routed,
        "num_branches": len(lora_bank.list_branches()),
    }


def _train_bank_no_router(
    *,
    segment: Segment,
    model: Any,
    lora: Any,
    lora_bank: LoRABank,
    drift: DriftDetector,
    lr: float,
    epochs: int,
    batch_size: int,
) -> Dict[str, Any]:
    """
    Baseline mode: bank + no router.

    - Uses drift detector to decide spawning new branch
    - Does NOT route per-example; always trains on the active branch
    - This baseline exists as baseline_name in config/code, without a new top-level folder.
    """

    if not lora_bank.list_branches():
        lora_bank.initialize(lora_wrapper=lora, initial_branch="b0", segment_id=segment.segment_id)

    # Train on current active branch
    train_metrics = _train_on_active_branch(
        segment=segment, model=model, lora=lora, lr=lr, epochs=epochs, batch_size=batch_size
    )

    # Update drift with a simple proxy signal from training accuracy
    signal = 1.0 - float(train_metrics.get("mean_batch_acc", 0.0))
    event = drift.update(signal=signal, segment_id=segment.segment_id)
    train_metrics["drift_triggered"] = bool(event.triggered)
    train_metrics["drift_score"] = float(event.score)

    if event.triggered:
        lora_bank.freeze_current_branch()
        new_b = lora_bank.spawn_new_branch(lora_wrapper=lora, segment_id=segment.segment_id)
        train_metrics["spawned_branch"] = new_b

    train_metrics["num_branches"] = len(lora_bank.list_branches())
    train_metrics["active_branch"] = lora_bank.get_active_branch() if lora_bank.list_branches() else ""
    return train_metrics


def _flatten_metrics(prefix: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for k, v in (metrics or {}).items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            flat[f"{prefix}.{k}"] = v
    return flat


def _format_prompt(instruction: str, input_text: str) -> str:
    input_text = (input_text or "").strip()
    if input_text:
        return f"指令：{instruction}\n输入：{input_text}\n输出："
    return f"指令：{instruction}\n输出："


if __name__ == "__main__":
    main()

