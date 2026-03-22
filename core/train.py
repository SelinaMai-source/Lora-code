from __future__ import annotations

import sys
import argparse
import csv
import json
import shutil
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
from core.methods.overlap_loss import compute_overlap_loss, compute_overlap_loss_torch
from core.methods.router import Router
from core.models.base_model import build_backbone
from core.models.lora_wrapper import build_lora_wrapper
from core.formatting import format_for_infer
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

    debug_tools = cfg.get("debug_tools", {}) if isinstance(cfg.get("debug_tools", {}), dict) else {}
    if bool(debug_tools.get("enable_overfit_8_mode", False)):
        _run_overfit_8_mode(
            cfg=cfg,
            stream=stream,
            backbone=backbone,
            lora=lora,
            run_paths=run_paths,
            logger=logger,
        )
        if bool(debug_tools.get("stop_after_overfit_mode", True)):
            logger.log("Stop after overfit_8_mode as requested.")
            return

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
    model_cfg = cfg.get("model", {}) if isinstance(cfg.get("model", {}), dict) else {}
    lr = float(train_cfg.get("lr", 1e-3))
    epochs = int(train_cfg.get("epochs_per_segment", 1))
    batch_size = int(train_cfg.get("batch_size", 1))
    eval_max_new_tokens = int(model_cfg.get("gen_max_new_tokens", 64))

    # Optional shared components (used by some baselines)
    lora_bank = LoRABank(max_branches=int(cfg.get("periodic", {}).get("max_branches", 8)) if isinstance(cfg.get("periodic", {}), dict) else 8)
    router = Router(cfg.get("router", {}) if isinstance(cfg.get("router", {}), dict) else {})
    drift = DriftDetector(cfg.get("drift", {}) if isinstance(cfg.get("drift", {}), dict) else {})

    method = _build_baseline_method(baseline_name, cfg)
    debug_tools = cfg.get("debug_tools", {}) if isinstance(cfg.get("debug_tools", {}), dict) else {}
    normalization_cfg = cfg.get("eval_normalization", {}) if isinstance(cfg.get("eval_normalization", {}), dict) else {}

    seen_segments: List[Segment] = []
    stream_segments = stream.stream
    if bool(debug_tools.get("enable_single_segment_mode", False)):
        target_segment_idx = int(debug_tools.get("single_segment_index", 0))
        stream_segments = [stream.stream[target_segment_idx]]
        logger.log(f"Single-segment mode enabled: segment_index={target_segment_idx}")
    for seg in stream_segments:
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

        # Evaluate on seen segments (unified)
        seen_segments.append(seg)
        eval_metrics = evaluate_stream(
            model=backbone,
            segments_seen=seen_segments,
            max_new_tokens=eval_max_new_tokens,
            router=router if baseline_name == "router_only" else None,
            lora_bank=lora_bank if baseline_name == "router_only" else None,
            segment_id=seg.segment_id,
            normalization_cfg=normalization_cfg,
            save_debug_examples_dir=str(Path(run_paths.run_dir) / "eval_debug"),
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
    model_cfg = cfg.get("model", {}) if isinstance(cfg.get("model", {}), dict) else {}
    lr = float(train_cfg.get("lr", 1e-4))
    epochs = int(train_cfg.get("epochs_per_segment", 1))
    batch_size = int(train_cfg.get("batch_size", 1))
    eval_max_new_tokens = int(model_cfg.get("gen_max_new_tokens", 64))

    drift = DriftDetector(cfg.get("drift", {}) if isinstance(cfg.get("drift", {}), dict) else {}) if use_drift else None
    bank_cfg = cfg.get("bank", {}) if isinstance(cfg.get("bank", {}), dict) else {}
    lora_bank = LoRABank(max_branches=int(bank_cfg.get("max_branches", 8))) if use_bank else None
    router = Router(cfg.get("router", {}) if isinstance(cfg.get("router", {}), dict) else {}) if use_router else None
    overlap_cfg = cfg.get("overlap", {}) if isinstance(cfg.get("overlap", {}), dict) else {}
    beta = float(overlap_cfg.get("beta", 0.1))
    normalization_cfg = cfg.get("eval_normalization", {}) if isinstance(cfg.get("eval_normalization", {}), dict) else {}

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
                use_overlap=use_overlap,
                beta=beta,
            )
        elif lora_bank is not None and router is None:
            # No router: always use the active branch
            train_metrics = _train_on_active_branch(
                segment=seg,
                model=backbone,
                lora=lora,
                lora_bank=lora_bank,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
                use_overlap=use_overlap,
                beta=beta,
            )
        else:
            # No bank: fall back to single default adapter
            if "default" in lora.list_adapters():
                lora.set_active_adapter("default")
            train_metrics = _train_on_active_branch(
                segment=seg,
                model=backbone,
                lora=lora,
                lora_bank=lora_bank,
                lr=lr,
                epochs=epochs,
                batch_size=batch_size,
                use_overlap=use_overlap,
                beta=beta,
            )

        # Optional overlap loss (logged as a scalar proxy)
        overlap_value = 0.0
        if use_overlap and lora_bank is not None:
            tok = getattr(backbone, "tokenizer", None)
            if tok is not None:
                anchor_prompts = [format_for_infer(tok, ex.instruction, ex.input) for ex in seg.eval[:8]]
            else:
                anchor_prompts = [f"{ex.instruction}\n\n{ex.input}" for ex in seg.eval[:8]]
            activations_by_branch: Dict[str, List[List[float]]] = {}
            for b in lora_bank.list_branches():
                lora.set_active_adapter(b)
                activations_by_branch[b] = backbone.get_activations(anchor_prompts)
            overlap_value = compute_overlap_loss(activations_by_branch=activations_by_branch, beta=beta)
            train_metrics["overlap_loss_proxy"] = float(overlap_value)

        logger.log(f"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}")

        # Evaluate
        seen_segments.append(seg)
        eval_metrics = evaluate_stream(
            model=backbone,
            segments_seen=seen_segments,
            max_new_tokens=eval_max_new_tokens,
            router=router if (router is not None and lora_bank is not None) else None,
            lora_bank=lora_bank if (router is not None and lora_bank is not None) else None,
            segment_id=seg.segment_id,
            normalization_cfg=normalization_cfg,
            save_debug_examples_dir=str(Path(run_paths.run_dir) / "eval_debug"),
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


def _train_on_active_branch(
    *,
    segment: Segment,
    model: Any,
    lora: Any,
    lora_bank: Optional[LoRABank],
    lr: float,
    epochs: int,
    batch_size: int,
    use_overlap: bool,
    beta: float,
) -> Dict[str, Any]:
    from baselines.sequential_lora.method import _batch

    pairs = [(ex.instruction, ex.input) for ex in segment.train]
    targets = [ex.output for ex in segment.train]

    batch_accs: List[float] = []
    batch_losses: List[float] = []
    batch_ans_accs: List[float] = []
    grad_norms: List[float] = []
    delta_norms: List[float] = []
    total_tokens = 0
    supervised_tokens = 0
    batches = 0
    for _ in range(max(1, epochs)):
        for b_pairs, b_targets in _batch(pairs, targets, batch_size):
            out = model.fit_batch(b_pairs, b_targets, lr=lr)

            # Anti-overlap regularization integrated into the training step.
            if (
                use_overlap
                and lora_bank is not None
                and beta > 0
                and hasattr(model, "get_activations_tensor")
                and len(lora_bank.list_branches()) > 1
            ):
                tok = getattr(model, "tokenizer", None)
                if tok is not None:
                    prompts = [format_for_infer(tok, ins, inp) for (ins, inp) in b_pairs]
                else:
                    prompts = [f"{ins}\n\n{inp}" for (ins, inp) in b_pairs]
                active_adapter = lora.get_active_adapter_name()
                activations_by_branch = {}
                for b in lora_bank.list_branches():
                    lora.set_active_adapter(b)
                    with_grad = b == active_adapter
                    acts = model.get_activations_tensor(prompts, with_grad=with_grad)
                    if not with_grad:
                        acts = acts.detach()
                    activations_by_branch[b] = acts
                lora.set_active_adapter(active_adapter)
                overlap_loss = compute_overlap_loss_torch(activations_by_branch=activations_by_branch, beta=beta)
                overlap_loss.backward()

            step_stats = lora.step_adapter()
            batch_accs.append(float(out.get("train_batch_acc", 0.0)))
            batch_losses.append(float(out.get("train_loss", 0.0)))
            batch_ans_accs.append(float(out.get("train_answer_token_acc", 0.0)))
            grad_norms.append(float(step_stats.get("grad_norm", 0.0)))
            delta_norms.append(float(step_stats.get("lora_param_delta_l2", 0.0)))
            total_tokens += int(out.get("num_total_tokens", 0))
            supervised_tokens += int(out.get("num_supervised_tokens", 0))
            batches += 1
    return {
        "batches": batches,
        "mean_batch_acc": sum(batch_accs) / max(1, len(batch_accs)),
        "train.loss": sum(batch_losses) / max(1, len(batch_losses)),
        "train.answer_token_acc": sum(batch_ans_accs) / max(1, len(batch_ans_accs)),
        "num_total_tokens": int(total_tokens),
        "num_supervised_tokens": int(supervised_tokens),
        "grad_norm": sum(grad_norms) / max(1, len(grad_norms)),
        "lora_param_delta_l2": sum(delta_norms) / max(1, len(delta_norms)),
        "lr": float(lr),
    }


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
    use_overlap: bool,
    beta: float,
) -> Dict[str, Any]:
    from baselines.sequential_lora.method import _batch

    pairs = [(ex.instruction, ex.input) for ex in segment.train]
    targets = [ex.output for ex in segment.train]

    routed = 0
    batch_accs: List[float] = []
    batch_losses: List[float] = []
    batch_ans_accs: List[float] = []
    grad_norms: List[float] = []
    delta_norms: List[float] = []
    total_tokens = 0
    supervised_tokens = 0
    batches = 0
    for _ in range(max(1, epochs)):
        for b_pairs, b_targets in _batch(pairs, targets, batch_size):
            for (ins, inp), y in zip(b_pairs, b_targets):
                tok = getattr(model, "tokenizer", None)
                prompt = format_for_infer(tok, ins, inp) if tok is not None else f"{ins}\n\n{inp}"
                decision = router.predict_branch(
                    prompt=prompt,
                    branch_names=lora_bank.list_branches(),
                    branch_meta=lora_bank.state_dict(),
                    segment_id=segment.segment_id,
                )
                lora.set_active_adapter(decision.branch_name)
                out = model.fit_batch([(ins, inp)], [y], lr=lr)

                # Anti-overlap integrated into training step (per routed example).
                if (
                    use_overlap
                    and beta > 0
                    and hasattr(model, "get_activations_tensor")
                    and len(lora_bank.list_branches()) > 1
                ):
                    active_adapter = lora.get_active_adapter_name()
                    activations_by_branch = {}
                    for b in lora_bank.list_branches():
                        lora.set_active_adapter(b)
                        with_grad = b == active_adapter
                        acts = model.get_activations_tensor([prompt], with_grad=with_grad)
                        if not with_grad:
                            acts = acts.detach()
                        activations_by_branch[b] = acts
                    lora.set_active_adapter(active_adapter)
                    overlap_loss = compute_overlap_loss_torch(activations_by_branch=activations_by_branch, beta=beta)
                    overlap_loss.backward()

                step_stats = lora.step_adapter()
                routed += 1
                batch_accs.append(float(out.get("train_batch_acc", 0.0)))
                batch_losses.append(float(out.get("train_loss", 0.0)))
                batch_ans_accs.append(float(out.get("train_answer_token_acc", 0.0)))
                grad_norms.append(float(step_stats.get("grad_norm", 0.0)))
                delta_norms.append(float(step_stats.get("lora_param_delta_l2", 0.0)))
                total_tokens += int(out.get("num_total_tokens", 0))
                supervised_tokens += int(out.get("num_supervised_tokens", 0))
            batches += 1
    return {
        "batches": batches,
        "mean_batch_acc": sum(batch_accs) / max(1, len(batch_accs)),
        "train.loss": sum(batch_losses) / max(1, len(batch_losses)),
        "train.answer_token_acc": sum(batch_ans_accs) / max(1, len(batch_ans_accs)),
        "num_total_tokens": int(total_tokens),
        "num_supervised_tokens": int(supervised_tokens),
        "grad_norm": sum(grad_norms) / max(1, len(grad_norms)),
        "lora_param_delta_l2": sum(delta_norms) / max(1, len(delta_norms)),
        "lr": float(lr),
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
        segment=segment,
        model=model,
        lora=lora,
        lora_bank=lora_bank,
        lr=lr,
        epochs=epochs,
        batch_size=batch_size,
        use_overlap=False,
        beta=0.0,
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


def _load_overfit_csv_rows(csv_path: Path) -> List[Dict[str, Any]]:
    """Reload partial overfit8_steps.csv for resume (typed columns)."""
    if not csv_path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row: Dict[str, Any] = {}
            for k, v in raw.items():
                if v is None or v == "":
                    continue
                try:
                    if k == "step" or k.endswith("_count"):
                        row[k] = int(float(v))
                    else:
                        row[k] = float(v)
                except ValueError:
                    row[k] = v
            rows.append(row)
    return rows


def _run_overfit_8_mode(
    *,
    cfg: Dict[str, Any],
    stream: ContinualStream,
    backbone: Any,
    lora: Any,
    run_paths: RunPaths,
    logger: SimpleLogger,
) -> None:
    from baselines.sequential_lora.method import _batch

    debug_tools = cfg.get("debug_tools", {}) if isinstance(cfg.get("debug_tools", {}), dict) else {}
    if not stream.stream:
        logger.log("overfit_8_mode skipped: empty stream.")
        return
    seg = stream.stream[int(debug_tools.get("overfit_segment_index", 0))]
    train_subset = seg.train[:8]
    if len(train_subset) < 1:
        logger.log("overfit_8_mode skipped: no train examples in selected segment.")
        return
    steps = int(debug_tools.get("overfit_steps", 200))
    log_every = int(debug_tools.get("overfit_log_every", 20))
    overfit_batch_size = int(debug_tools.get("overfit_batch_size", 1))
    model_cfg = cfg.get("model", {}) if isinstance(cfg.get("model", {}), dict) else {}
    overfit_gen_max_new_tokens = int(debug_tools.get("overfit_gen_max_new_tokens", model_cfg.get("gen_max_new_tokens", 64)))
    lr = float((cfg.get("train", {}) or {}).get("lr", 2e-4))
    out_dir = Path(run_paths.run_dir) / "debug" / "overfit8"
    ensure_dir(str(out_dir))
    ckpt_root = out_dir / "lora_ckpt"
    state_path = out_dir / "overfit_state.json"
    csv_path = out_dir / "overfit8_steps.csv"
    resume = bool(debug_tools.get("overfit_resume", False))
    fresh = bool(debug_tools.get("overfit_fresh_start", False))
    decode_only = bool(debug_tools.get("overfit_decode_ablation_only", False))
    if fresh and not resume and not decode_only:
        if ckpt_root.is_dir():
            shutil.rmtree(ckpt_root, ignore_errors=True)
        for p in (state_path, csv_path):
            if p.is_file():
                p.unlink()
        for p in (out_dir / "first_token_margin_over_time.csv", out_dir / "prefix_rollout_summary.csv"):
            if p.is_file():
                p.unlink()

    snapshot_every = int(debug_tools.get("overfit_checkpoint_every", 0))
    if snapshot_every <= 0:
        snapshot_every = max(1, log_every)

    generation_ablation_out_csv = Path(run_paths.run_dir) / "debug" / "generation_prompt_ablation.csv"
    generation_ablation_out_cont_json = Path(run_paths.run_dir) / "debug" / "generation_prompt_ablation_cont_heads.json"

    normalization_cfg = cfg.get("eval_normalization", {}) if isinstance(cfg.get("eval_normalization", {}), dict) else {}

    start_step = 1
    per_step_rows: List[Dict[str, Any]] = []
    if resume and state_path.is_file():
        try:
            st = json.loads(state_path.read_text(encoding="utf-8"))
            last_done = int(st.get("last_completed_step", 0))
            start_step = last_done + 1
            latest = ckpt_root / "latest"
            snap = ckpt_root / f"step_{last_done:06d}"
            load_path = latest if latest.is_dir() else snap
            if load_path.is_dir() and hasattr(lora, "load_adapter_checkpoint"):
                lora.load_adapter_checkpoint(str(load_path))
                logger.log(
                    f"[overfit8] Resume: loaded LoRA from {load_path} "
                    f"(last_completed_step={last_done}), continue from step {start_step}."
                )
            else:
                logger.log(
                    f"[overfit8] Resume requested but no adapter at {latest} or {snap}; "
                    "starting from step 1."
                )
                start_step = 1
        except Exception as e:
            logger.log(f"[overfit8] Resume parse/load failed ({e}); starting from step 1.")
            start_step = 1

    if start_step > 1 and csv_path.is_file():
        per_step_rows = [r for r in _load_overfit_csv_rows(csv_path) if int(r.get("step", 0)) < start_step]
        logger.log(f"[overfit8] Restored {len(per_step_rows)} CSV rows for steps < {start_step}.")
    elif start_step > 1 and not csv_path.is_file():
        logger.log(
            "[overfit8] Warning: resume without overfit8_steps.csv; metrics history will only "
            f"contain steps >= {start_step}."
        )

    if start_step > steps:
        logger.log(f"[overfit8] Nothing to do: resume start_step={start_step} > overfit_steps={steps}.")
        return

    hf_ok = getattr(backbone, "tokenizer", None) is not None and getattr(backbone, "model", None) is not None
    diag_enabled = hf_ok and bool(debug_tools.get("enable_sequence_behavior_diagnosis", False))
    # Staged diagnosis (YAML toggles). Steps 1→5: failure+first_token → prefix → decode → ladder.
    run_failure_decomposition = diag_enabled and bool(debug_tools.get("run_failure_decomposition", True))
    run_first_token_audit = diag_enabled and bool(debug_tools.get("run_first_token_audit", True))
    run_prefix_rollout = diag_enabled and bool(debug_tools.get("run_prefix_rollout", False))
    if run_prefix_rollout and not hasattr(backbone, "generate_with_forced_answer_prefix"):
        logger.log("[overfit8] run_prefix_rollout requested but backbone has no generate_with_forced_answer_prefix; skipping.")
        run_prefix_rollout = False
    run_decode_ablation = diag_enabled and bool(debug_tools.get("run_decode_ablation", False))
    run_overfit_ladder = diag_enabled and bool(debug_tools.get("run_overfit_ladder", False))
    ladder_steps = int(debug_tools.get("overfit_ladder_steps", steps))
    ladder_init_path = str(ckpt_root / "ladder_init_adapter")

    if diag_enabled:
        logger.log(
            "[overfit8] Sequence behavior diagnosis: "
            f"failure={run_failure_decomposition} first_token={run_first_token_audit} "
            f"prefix_rollout={run_prefix_rollout} decode_ablation={run_decode_ablation} "
            f"overfit_ladder={run_overfit_ladder}. "
            "(Open-loop vs teacher-forced gap; not mask/shift debugging.)"
        )

    if decode_only:
        if not diag_enabled:
            logger.log("[overfit8] decode_ablation_only: requires HF tokenizer+model and enable_sequence_behavior_diagnosis.")
            return
        if not run_decode_ablation:
            logger.log("[overfit8] decode_ablation_only: set run_decode_ablation: true in debug_tools.")
            return
        ckpt_rel = str(debug_tools.get("overfit_decode_ablation_ckpt", "lora_ckpt/step_000020"))
        ckpt_abs = (out_dir / ckpt_rel).resolve()
        if not ckpt_abs.is_dir():
            logger.log(f"[overfit8] decode_ablation_only: missing adapter directory {ckpt_abs}")
            return
        if not hasattr(lora, "load_adapter_checkpoint"):
            logger.log("[overfit8] decode_ablation_only: LoRA wrapper has no load_adapter_checkpoint.")
            return
        pairs = [(ex.instruction, ex.input) for ex in train_subset]
        lora.load_adapter_checkpoint(str(ckpt_abs))
        logger.log(
            f"[overfit8] decode_ablation_only: loaded {ckpt_abs}; "
            f"eval greedy/beam2/beam4 (do_sample=false), max_new_tokens={overfit_gen_max_new_tokens}"
        )
        from core.overfit_sequence_diagnostics import run_decode_ablation

        infer_prompts_final = [
            format_for_infer(backbone.tokenizer, ins, inp, add_generation_prompt=True) for (ins, inp) in pairs
        ]
        run_decode_ablation(
            out_dir=out_dir,
            examples=list(train_subset),
            infer_prompts=infer_prompts_final,
            backbone=backbone,
            max_new_tokens=overfit_gen_max_new_tokens,
            normalization_cfg=normalization_cfg,
        )
        logger.log("[overfit8] Wrote decode_ablation.json / decode_ablation.csv (decode_ablation_only).")
        return

    logger.log(
        f"[overfit8] segment={seg.segment_id}:{seg.segment_name} examples={len(train_subset)} "
        f"steps={steps} log_every={log_every} start_step={start_step} resume={resume}"
    )

    pairs = [(ex.instruction, ex.input) for ex in train_subset]
    targets = [ex.output for ex in train_subset]

    if start_step == 1 and not resume and hasattr(lora, "save_adapter_checkpoint"):
        ensure_dir(str(ckpt_root))
        lora.save_adapter_checkpoint(ladder_init_path)
        logger.log(f"[overfit8] Saved ladder_init adapter (pre-training) to {ladder_init_path}")

    if (
        getattr(backbone, "tokenizer", None) is not None
        and getattr(backbone, "model", None) is not None
        and start_step <= 1
    ):
        from core.debug_teacher_audit import dump_overfit_teacher_audit

        if bool(debug_tools.get("dump_teacher_forced_audit", True)):
            dump_overfit_teacher_audit(
                backbone=backbone,
                examples=list(train_subset),
                out_path=str(out_dir / "teacher_forced_audit_initial.json"),
                strict_assertions=bool(debug_tools.get("strict_teacher_metric_assertions", False)),
            )

    from core.debug_teacher_audit import mean_teacher_forced_over_examples
    from core.evaluate import _lcs_overlap, _normalize, _token_f1
    for step in range(start_step, steps + 1):
        # Train repeatedly on the same 8 examples in tiny batches to avoid OOM.
        step_loss_sum = 0.0
        step_ans_acc_sum = 0.0
        step_grad_sum = 0.0
        step_delta_sum = 0.0
        step_total_tokens = 0
        step_supervised_tokens = 0
        step_loss_tokens = 0
        step_inner_batches = 0
        for b_pairs, b_targets in _batch(pairs, targets, overfit_batch_size):
            out = backbone.fit_batch(b_pairs, b_targets, lr=lr)
            step_stats = lora.step_adapter()
            step_loss_sum += float(out.get("train_loss", 0.0))
            step_ans_acc_sum += float(out.get("train_answer_token_acc", 0.0))
            step_grad_sum += float(step_stats.get("grad_norm", 0.0))
            step_delta_sum += float(step_stats.get("lora_param_delta_l2", 0.0))
            step_total_tokens += int(out.get("num_total_tokens", 0))
            step_supervised_tokens += int(out.get("num_supervised_tokens", 0))
            step_loss_tokens += int(out.get("num_loss_tokens", 0))
            step_inner_batches += 1
        row = {
            "step": step,
            "train_loss": step_loss_sum / max(1, step_inner_batches),
            "train_answer_token_acc": step_ans_acc_sum / max(1, step_inner_batches),
            "num_total_tokens": int(step_total_tokens),
            "num_supervised_tokens": int(step_supervised_tokens),
            "num_loss_tokens": int(step_loss_tokens),
            "grad_norm": step_grad_sum / max(1, step_inner_batches),
            "lora_param_delta_l2": step_delta_sum / max(1, step_inner_batches),
            "lr": float(lr),
        }
        per_step_rows.append(row)

        if step % max(1, log_every) == 0 or step == 1 or step == steps:
            tok = getattr(backbone, "tokenizer", None)
            infer_prompts = (
                [format_for_infer(tok, ins, inp, add_generation_prompt=True) for (ins, inp) in pairs]
                if tok is not None
                else [f"{ins}\n\n{inp}" for (ins, inp) in pairs]
            )
            preds = backbone.generate(infer_prompts, max_new_tokens=overfit_gen_max_new_tokens)
            side_by_side = []
            exact_match_cnt = 0
            prefix1_match_cnt = 0
            prefix3_match_cnt = 0
            prefix5_match_cnt = 0
            token_f1_list: List[float] = []
            lcs_list: List[float] = []
            for i, (ex, pred, infer_prompt) in enumerate(zip(train_subset, preds, infer_prompts)):
                norm_pred = _normalize(pred or "", prompt=infer_prompt, cfg=normalization_cfg)
                norm_gold = _normalize(ex.output or "", prompt=infer_prompt, cfg=normalization_cfg)
                is_match = bool(norm_pred == norm_gold)
                if is_match:
                    exact_match_cnt += 1
                pred_tokens = [t for t in norm_pred.split() if t]
                gold_tokens = [t for t in norm_gold.split() if t]
                prefix1_match_cnt += int(pred_tokens[:1] == gold_tokens[:1])
                prefix3_match_cnt += int(pred_tokens[:3] == gold_tokens[:3])
                prefix5_match_cnt += int(pred_tokens[:5] == gold_tokens[:5])
                token_f1_list.append(float(_token_f1(norm_pred, norm_gold)))
                lcs_list.append(float(_lcs_overlap(norm_pred, norm_gold)))
                side_by_side.append(
                    {
                        "idx": i,
                        "instruction": ex.instruction,
                        "input": ex.input,
                        "gold_output": ex.output,
                        "formatted_infer_prompt": infer_prompt,
                        "generated_output": pred,
                        "normalized_prediction": norm_pred,
                        "normalized_gold": norm_gold,
                        "exact_match": is_match,
                        "prefix_1_match": bool(pred_tokens[:1] == gold_tokens[:1]),
                        "prefix_3_match": bool(pred_tokens[:3] == gold_tokens[:3]),
                        "prefix_5_match": bool(pred_tokens[:5] == gold_tokens[:5]),
                        "token_f1": float(token_f1_list[-1]),
                        "lcs_overlap": float(lcs_list[-1]),
                    }
                )
            tf_loss_m, tf_acc_m, _n_tf = mean_teacher_forced_over_examples(
                backbone=backbone, pairs=pairs, targets=targets
            )
            row["teacher_forced_loss_mean"] = float(tf_loss_m)
            row["teacher_forced_shifted_token_acc_mean"] = float(tf_acc_m)
            row["token_f1_mean"] = float(sum(token_f1_list) / max(1, len(token_f1_list)))
            row["lcs_overlap_mean"] = float(sum(lcs_list) / max(1, len(lcs_list)))
            save_json(str(out_dir / f"step_{step:04d}_predictions.json"), side_by_side)
            row["exact_match_count"] = int(exact_match_cnt)
            row["prefix1_acc"] = float(prefix1_match_cnt / max(1, len(side_by_side)))
            row["prefix3_acc"] = float(prefix3_match_cnt / max(1, len(side_by_side)))
            row["prefix5_acc"] = float(prefix5_match_cnt / max(1, len(side_by_side)))
            logger.log(
                f"[overfit8] step={step} loss={row['train_loss']:.6f} "
                f"answer_token_acc={row['train_answer_token_acc']:.4f} "
                f"tf_shifted_acc={row['teacher_forced_shifted_token_acc_mean']:.4f} "
                f"grad_norm={row['grad_norm']:.6f} delta={row['lora_param_delta_l2']:.6f} "
                f"exact_match={exact_match_cnt}/{len(side_by_side)} "
                f"prefix1={prefix1_match_cnt}/{len(side_by_side)} "
                f"prefix3={prefix3_match_cnt}/{len(side_by_side)} "
                f"prefix5={prefix5_match_cnt}/{len(side_by_side)}"
            )
            if run_failure_decomposition or run_first_token_audit or run_prefix_rollout:
                from core.overfit_sequence_diagnostics import (
                    run_failure_decomposition_step,
                    run_first_token_audit_step,
                    run_prefix_rollout_step,
                )

                if run_failure_decomposition:
                    run_failure_decomposition_step(
                        step=step,
                        out_dir=out_dir,
                        examples=train_subset,
                        preds=preds,
                        infer_prompts=infer_prompts,
                        normalization_cfg=normalization_cfg,
                    )
                if run_first_token_audit:
                    run_first_token_audit_step(
                        step=step,
                        out_dir=out_dir,
                        examples=train_subset,
                        infer_prompts=infer_prompts,
                        backbone=backbone,
                    )
                if run_prefix_rollout:
                    run_prefix_rollout_step(
                        step=step,
                        out_dir=out_dir,
                        examples=train_subset,
                        infer_prompts=infer_prompts,
                        backbone=backbone,
                        max_new_tokens=overfit_gen_max_new_tokens,
                        normalization_cfg=normalization_cfg,
                    )

        state_path.write_text(
            json.dumps({"last_completed_step": step, "overfit_steps": steps}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        save_csv(str(csv_path), per_step_rows)
        # Always refresh latest/ each step so resume matches overfit_state.json.
        if hasattr(lora, "save_adapter_checkpoint"):
            ensure_dir(str(ckpt_root))
            lora.save_adapter_checkpoint(str(ckpt_root / "latest"))
        if snapshot_every > 0 and (step % snapshot_every == 0 or step == steps or step == 1):
            ensure_dir(str(ckpt_root))
            if hasattr(lora, "save_adapter_checkpoint"):
                lora.save_adapter_checkpoint(str(ckpt_root / f"step_{step:06d}"))

    save_csv(str(csv_path), per_step_rows)

    post_overfit_adapter = str(ckpt_root / "post_overfit_adapter")
    if diag_enabled and (run_decode_ablation or run_overfit_ladder) and hasattr(lora, "save_adapter_checkpoint"):
        ensure_dir(str(ckpt_root))
        lora.save_adapter_checkpoint(post_overfit_adapter)
        logger.log(f"[overfit8] Saved post-overfit adapter for decode/ladder restore: {post_overfit_adapter}")

    if diag_enabled and run_decode_ablation:
        from core.overfit_sequence_diagnostics import run_decode_ablation

        infer_prompts_final = [
            format_for_infer(backbone.tokenizer, ins, inp, add_generation_prompt=True) for (ins, inp) in pairs
        ]
        run_decode_ablation(
            out_dir=out_dir,
            examples=list(train_subset),
            infer_prompts=infer_prompts_final,
            backbone=backbone,
            max_new_tokens=overfit_gen_max_new_tokens,
            normalization_cfg=normalization_cfg,
        )
        logger.log("[overfit8] Wrote decode_ablation.json / decode_ablation.csv")

    if diag_enabled and run_overfit_ladder:
        from core.overfit_sequence_diagnostics import run_overfit_ladder

        infer_prompts_final = [
            format_for_infer(backbone.tokenizer, ins, inp, add_generation_prompt=True) for (ins, inp) in pairs
        ]
        run_overfit_ladder(
            ladder_sizes=(1, 2, 4, 8),
            ladder_steps=ladder_steps,
            pairs=pairs,
            targets=targets,
            train_subset=list(train_subset),
            infer_prompts=infer_prompts_final,
            backbone=backbone,
            lora=lora,
            lr=lr,
            overfit_batch_size=overfit_batch_size,
            overfit_gen_max_new_tokens=overfit_gen_max_new_tokens,
            normalization_cfg=normalization_cfg,
            ladder_init_adapter_path=ladder_init_path,
            out_csv=out_dir / "overfit_ladder.csv",
            logger=logger,
        )
        logger.log("[overfit8] Wrote overfit_ladder.csv")

    if diag_enabled and Path(post_overfit_adapter).is_dir() and hasattr(lora, "load_adapter_checkpoint"):
        lora.load_adapter_checkpoint(post_overfit_adapter)
        logger.log("[overfit8] Restored post-overfit adapter after decode/ladder.")

    if diag_enabled:
        from core.overfit_sequence_diagnostics import write_sequence_behavior_report

        results_dir = str(cfg.get("paths", {}).get("results_dir", "results"))
        experiment_name = str(cfg.get("experiment_name", "experiment"))
        write_sequence_behavior_report(
            run_dir=Path(run_paths.run_dir),
            results_dir=Path(results_dir),
            experiment_name=experiment_name,
            run_id=run_paths.run_id,
        )
        logger.log(
            f"[overfit8] Wrote sequence behavior report: "
            f"{Path(results_dir) / 'debug_report_sequence_behavior_diagnosis.md'}"
        )

    if getattr(backbone, "tokenizer", None) is not None and getattr(backbone, "model", None) is not None:
        from core.debug_teacher_audit import dump_overfit_teacher_audit

        if bool(debug_tools.get("dump_teacher_forced_audit", True)):
            dump_overfit_teacher_audit(
                backbone=backbone,
                examples=list(train_subset),
                out_path=str(out_dir / "teacher_forced_audit_final.json"),
                strict_assertions=bool(debug_tools.get("strict_teacher_metric_assertions", False)),
            )

    # Final A/B generation prompt ablation on the same 8 overfit samples.
    # Variant A: add_generation_prompt=True
    # Variant B: add_generation_prompt=False (may have no effect depending on the chat template).
    tok = getattr(backbone, "tokenizer", None)
    if tok is not None and hasattr(backbone, "generate_with_ids"):
        infer_prompts_a = [format_for_infer(tok, ins, inp, add_generation_prompt=True) for (ins, inp) in pairs]
        infer_prompts_b = [format_for_infer(tok, ins, inp, add_generation_prompt=False) for (ins, inp) in pairs]

        audit_a = backbone.generate_with_ids(infer_prompts_a, max_new_tokens=overfit_gen_max_new_tokens)
        audit_b = backbone.generate_with_ids(infer_prompts_b, max_new_tokens=overfit_gen_max_new_tokens)
        preds_a = [x.get("raw_generated_text", "") for x in audit_a]
        preds_b = [x.get("raw_generated_text", "") for x in audit_b]

        def _compute_metrics(preds: List[str], prompts_local: List[str]) -> Dict[str, Any]:
            exact = 0
            p1 = 0
            p3 = 0
            p5 = 0
            for ex, pred, pr in zip(train_subset, preds, prompts_local):
                n_pred = _normalize(pred or "", prompt=pr, cfg=normalization_cfg)
                n_gold = _normalize(ex.output or "", prompt=pr, cfg=normalization_cfg)
                if n_pred == n_gold:
                    exact += 1
                pred_tokens = [t for t in n_pred.split() if t]
                gold_tokens = [t for t in n_gold.split() if t]
                p1 += int(pred_tokens[:1] == gold_tokens[:1])
                p3 += int(pred_tokens[:3] == gold_tokens[:3])
                p5 += int(pred_tokens[:5] == gold_tokens[:5])
            return {
                "exact_match_count": int(exact),
                "prefix1_acc": float(p1 / max(1, len(train_subset))),
                "prefix3_acc": float(p3 / max(1, len(train_subset))),
                "prefix5_acc": float(p5 / max(1, len(train_subset))),
            }

        m_a = _compute_metrics(preds_a, infer_prompts_a)
        m_b = _compute_metrics(preds_b, infer_prompts_b)

        save_csv(
            str(generation_ablation_out_csv),
            [
                {"variant": "A_add_generation_prompt_true", **m_a},
                {"variant": "B_add_generation_prompt_false", **m_b},
            ],
        )

        cont_head_rows: List[Dict[str, Any]] = []
        head_match_cnt = 0
        for i, ex in enumerate(train_subset):
            a_head = (audit_a[i].get("decoded_continuation_head", "") or "")
            b_head = (audit_b[i].get("decoded_continuation_head", "") or "")
            a_tokens = [t for t in _normalize(a_head, prompt="", cfg=normalization_cfg).split() if t]
            b_tokens = [t for t in _normalize(b_head, prompt="", cfg=normalization_cfg).split() if t]
            match5 = bool(a_tokens[:5] == b_tokens[:5])
            head_match_cnt += int(match5)
            cont_head_rows.append(
                {
                    "idx": i,
                    "gold_output": ex.output,
                    "A_decoded_continuation_head": a_head,
                    "B_decoded_continuation_head": b_head,
                    "head_prefix5_match": match5,
                }
            )
        generation_ablation_out_cont_json.write_text(
            json.dumps(
                {
                    "continuation_head_prefix5_match_rate": float(head_match_cnt / max(1, len(train_subset))),
                    "rows": cont_head_rows,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()

