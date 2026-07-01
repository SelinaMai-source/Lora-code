#!/usr/bin/env python3
"""
LFPT5 continual-learning bridge for CITB streams exported by run_lfpt5_published_setting.py.

Runs inside conda env ``lfll_1`` (T5 + fairscale-free single-GPU training).
Uses Summarization/{model,dataset,utils}.py and scores with core.evaluate helpers.
"""
from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import pickle
import random
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers.optimization import Adafactor

BRIDGE_DIR = Path(__file__).resolve().parent
REPO = BRIDGE_DIR.parents[2]
SUM_DIR = REPO / "external_baselines/lfpt5/Summarization"
CLS_DIR = REPO / "external_baselines/lfpt5/Classification"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(SUM_DIR) not in sys.path:
    sys.path.insert(0, str(SUM_DIR))

from core.evaluate import _normalize, _token_f1  # noqa: E402
from core.utils import append_jsonl, save_csv, save_json  # noqa: E402
from core.wandb_tracker import WandbTracker  # noqa: E402
from dataset import SmartBatchingCollate, T5SummarizationDataset  # noqa: E402
from model import T5forSummarization  # noqa: E402
from utils import seed_everything  # noqa: E402

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("lfpt5_citb_bridge")


def _format_input(example: Dict[str, Any]) -> str:
    ins = str(example.get("instruction", "") or "").strip()
    inp = str(example.get("input", "") or "").strip()
    if ins and inp:
        return f"{ins}\n\n{inp}"
    return ins or inp


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {path}")
    return data


def _tsv_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _tsv_unescape(value: str) -> str:
    out: List[str] = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt == "t":
                out.append("\t")
                i += 2
                continue
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "r":
                out.append("\r")
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
        out.append(value[i])
        i += 1
    return "".join(out)


def _write_tsv(path: Path, rows: Sequence[Tuple[int, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for task_idx, src, tgt in rows:
            f.write(f"{task_idx}\t{_tsv_escape(src)}\t{_tsv_escape(tgt)}\n")


class CITBT5SummarizationDataset(T5SummarizationDataset):
    """LFPT5 TSV reader with escaped newlines/tabs from CITB export."""

    def getalldata(self, filename):  # type: ignore[override]
        alldata: List[List[str]] = []
        alllmdata: List[List[str]] = []
        ifmem: List[int] = []
        with open(filename, "r", encoding="utf-8") as f:
            for oneline in f:
                oneline = oneline.rstrip("\n")
                if not oneline:
                    continue
                linelist = oneline.split("\t")
                if len(linelist) != 3:
                    raise ValueError(f"Malformed TSV line in {filename}: {oneline[:120]!r}")
                typeindex = int(linelist[0])
                src = _tsv_unescape(linelist[1])
                tgt = _tsv_unescape(linelist[2])
                ifmem.append(0 if typeindex < self.currenttasknumber else 1)
                alldata.append([src, tgt])
                alllmdata.append(
                    [self.gentasktoken[typeindex], f"{src} {self.answertoken} {tgt}"]
                )
        return alldata, alllmdata, ifmem


def _json_examples_to_rows(examples: Sequence[Dict[str, Any]], task_idx: int) -> List[Tuple[int, str, str]]:
    return [(task_idx, _format_input(ex), str(ex.get("output", "") or "")) for ex in examples]


def _ordered_unique_outputs(examples: Sequence[Dict[str, Any]]) -> List[str]:
    labels: List[str] = []
    seen = set()
    for ex in examples:
        label = str(ex.get("output", "") or "").strip()
        if label and label not in seen:
            labels.append(label)
            seen.add(label)
    return labels


def _is_classification_stream(cfg: Dict[str, Any]) -> bool:
    lfpt5_cfg = cfg.get("lfpt5") or {}
    explicit = str(lfpt5_cfg.get("task_family", "") or "").strip().lower()
    if explicit:
        return explicit in {"classification", "classify", "seqglue"}
    stream_name = str((cfg.get("data") or {}).get("stream_name", "") or "").strip().lower()
    benchmark = str((cfg.get("paper") or {}).get("benchmark_alias", "") or "").strip().lower()
    return stream_name == "seqglue" or benchmark == "seqglue"


def _init_prompt_embedding(
    model: T5forSummarization,
    tokenizer: T5Tokenizer,
    prompt_number: int,
    task_name: str,
    *,
    classification_labels: Optional[Sequence[str]] = None,
) -> torch.Tensor:
    """Mirror LFPT5 prompt initialization, using classification label verbalizers when needed."""
    t5_embedding = model.model.get_input_embeddings()
    prompt_init_embedding = torch.FloatTensor(prompt_number, t5_embedding.weight.size(1))
    seed_texts = ["summarization", task_name]
    token_stats_dir = SUM_DIR
    if classification_labels:
        seed_texts = ["sentence classification", task_name, *classification_labels]
        token_stats_dir = CLS_DIR
    if len(seed_texts) > prompt_number:
        raise ValueError(f"prompt_number={prompt_number} is too small for prompt seeds: {seed_texts}")

    logger.info("LFPT5 prompt init seeds: %s", seed_texts)
    startindex = 0
    for text in seed_texts:
        encoded = tokenizer.batch_encode_plus([text], padding=False, truncation=False, return_tensors="pt")
        token_ids = encoded["input_ids"].squeeze()[:-1]
        embedding = t5_embedding(token_ids).clone().detach()
        if embedding.shape[0] > 1:
            embedding = torch.mean(embedding, 0, keepdim=True)
        prompt_init_embedding[startindex] = embedding
        startindex += 1

    with (token_stats_dir / "allnumber.pickle").open("rb") as f:
        all_tokens = pickle.load(f)
    sorted_tokens = sorted(all_tokens.items(), key=lambda item: item[1], reverse=True)
    top5000 = []
    for token_id, count in sorted_tokens:
        if token_id == 2:
            continue
        top5000.append((token_id, count))
        if len(top5000) >= 5000:
            break
    for token_id, _count in random.sample(top5000, prompt_number - len(seed_texts)):
        prompt_init_embedding[startindex] = t5_embedding.weight[token_id].clone().detach()
        startindex += 1
    return prompt_init_embedding


def discover_segments(export_dir: Path) -> List[Tuple[int, str, Path]]:
    segs: List[Tuple[int, str, Path]] = []
    for d in sorted(export_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("segment_"):
            continue
        parts = d.name.split("_", 2)
        if len(parts) < 2:
            continue
        sid = int(parts[1])
        segs.append((sid, d.name, d))
    return sorted(segs, key=lambda x: x[0])


def _get_dataloader(
    num_workers: int,
    dataset: T5SummarizationDataset,
    batch_size: int,
    max_len: int,
    sampler,
) -> DataLoader:
    collate_fn = SmartBatchingCollate(max_length=max_len, pad_token_id=dataset.tokenizer.pad_token_id)
    return DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        sampler=sampler,
        collate_fn=collate_fn,
        drop_last=False,
        num_workers=num_workers,
        pin_memory=True,
    )


def _train_single_gpu(
    args: SimpleNamespace,
    model: T5forSummarization,
    train_dataset: T5SummarizationDataset,
) -> Dict[str, float]:
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    train_sampler = RandomSampler(train_dataset)
    train_dataloader = _get_dataloader(
        args.num_workers,
        train_dataset,
        args.batch_size_per_gpu,
        args.max_length,
        train_sampler,
    )
    optimizer = Adafactor(
        trainable_params,
        lr=args.lr,
        clip_threshold=args.max_grad_norm,
        decay_rate=-0.8,
        weight_decay=args.weight_decay,
        scale_parameter=False,
        relative_step=False,
    )
    model.train()
    all_loss: List[float] = []
    all_lm: List[float] = []
    all_kd: List[float] = []
    grad_accum = max(1, int(args.gradient_accumulation_steps))
    optimizer.zero_grad()
    for _epoch in range(args.max_epoch):
        for step, batch in enumerate(train_dataloader):
            inputs = {
                "input_ids": batch[0].to(args.device),
                "attention_mask": batch[1].to(args.device),
                "target_ids": batch[2].to(args.device),
                "target_mask": batch[3].to(args.device),
                "ifmem": batch[8].to(args.device),
            }
            inputs_lm = {
                "input_ids": batch[4].to(args.device),
                "attention_mask": batch[5].to(args.device),
                "target_ids": batch[6].to(args.device),
                "target_mask": batch[7].to(args.device),
            }
            loss, kdloss = model(inputs, ifcalpre=True)
            lmloss = model(inputs_lm, ifcalpre=False) * args.lm_lambda
            finalloss = (loss + lmloss) * (1.0 - args.kd_lamda) + kdloss * args.kd_lamda
            loss_values = {
                "loss": loss,
                "lm_loss": lmloss,
                "kd_loss": kdloss,
                "final_loss": finalloss,
            }
            bad_losses = [name for name, value in loss_values.items() if not torch.isfinite(value).all()]
            if bad_losses:
                details = ", ".join(f"{name}={float(value.detach().cpu().item())}" for name, value in loss_values.items())
                raise FloatingPointError(
                    f"Non-finite LFPT5 loss at epoch={_epoch} step={step}: {details}; bad={bad_losses}"
                )
            (finalloss / grad_accum).backward()
            if (step + 1) % grad_accum == 0 or step == len(train_dataloader) - 1:
                bad_grads = [
                    idx
                    for idx, param in enumerate(trainable_params)
                    if param.grad is not None and not torch.isfinite(param.grad).all()
                ]
                if bad_grads:
                    raise FloatingPointError(
                        f"Non-finite LFPT5 gradient at epoch={_epoch} step={step}: param_indices={bad_grads[:8]}"
                    )
                optimizer.step()
                optimizer.zero_grad()
            all_loss.append(float(loss.item()))
            all_lm.append(float(lmloss.item()))
            all_kd.append(float(kdloss.item()))
    return {
        "train_loss_mean": float(np.mean(all_loss)) if all_loss else 0.0,
        "train_lm_loss_mean": float(np.mean(all_lm)) if all_lm else 0.0,
        "train_kd_loss_mean": float(np.mean(all_kd)) if all_kd else 0.0,
        "train_steps": float(len(all_loss)),
    }


def _assert_finite_prompt(model: T5forSummarization, *, context: str) -> None:
    prompt = model.promptembedding
    if prompt is None:
        raise FloatingPointError(f"Missing LFPT5 prompt embedding before {context}")
    if not torch.isfinite(prompt).all():
        raise FloatingPointError(f"Non-finite LFPT5 prompt embedding before {context}")


def _save_prompt_ckpt(model: T5forSummarization, path: Path) -> None:
    _assert_finite_prompt(model, context=f"saving {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "promptnumber": model.promptnumber,
            "promptembedding": model.promptembedding.detach().cpu(),
        },
        path,
    )


def _load_prompt_ckpt(model: T5forSummarization, path: Path, expected_prompt_number: int) -> None:
    ckpt = torch.load(str(path), map_location="cpu")
    if int(ckpt["promptnumber"]) != expected_prompt_number:
        raise ValueError(
            f"Prompt size mismatch: ckpt={ckpt['promptnumber']} expected={expected_prompt_number}"
        )
    model.set_prompt_embedding(expected_prompt_number, ckpt["promptembedding"])


def _generate_pseudo_memory(
    args: SimpleNamespace,
    model: T5forSummarization,
    tokenizer: T5Tokenizer,
    gentasktokens: Sequence[str],
    answertoken: str,
    prev_task_idx: int,
    source_tsv: Path,
    mem_dir: Path,
    mem_per_task: int,
) -> None:
    mem_dir.mkdir(parents=True, exist_ok=True)
    _assert_finite_prompt(model, context=f"pseudo-memory generation for task {prev_task_idx}")
    pretest = CITBT5SummarizationDataset(
        str(source_tsv), args.max_length, tokenizer, list(gentasktokens), answertoken, prev_task_idx
    )
    pretest_loader = _get_dataloader(
        args.num_workers,
        pretest,
        min(32, args.valid_size_per_gpu),
        args.max_length,
        SequentialSampler(pretest),
    )
    model.eval()
    samples: List[str] = []
    with torch.no_grad():
        for step, batch in enumerate(pretest_loader):
            if step > 2:
                break
            inputs_lm = {
                "input_ids": batch[4].to(args.device),
                "attention_mask": batch[5].to(args.device),
                "target_ids": batch[6].to(args.device),
                "target_mask": batch[7].to(args.device),
            }
            _sen, _target, preds = model._generative_samples(inputs_lm)
            for pred in preds:
                parts = pred.split(answertoken)
                onesen = parts[0].strip(" ")
                if len(onesen.split(" ")) >= 256:
                    onesum = ""
                    num = 0
                    for word in onesen.split(" "):
                        if not word:
                            continue
                        onesum = onesum + word + " "
                        if word.endswith("."):
                            num += 1
                        if num >= 3:
                            break
                    samples.append(f"{_tsv_escape(onesen)}\t{_tsv_escape(onesum.strip(' '))}")
                elif len(parts) == 2:
                    samples.append(f"{_tsv_escape(parts[0].strip(' '))}\t{_tsv_escape(parts[1].strip(' '))}")
    model.train()
    if 2 * mem_per_task < len(samples):
        chosen = random.sample(samples, 2 * mem_per_task)
    else:
        chosen = samples
    train_mem = chosen[:mem_per_task]
    valid_mem = chosen[mem_per_task:]
    with (mem_dir / "train_mem.txt").open("w", encoding="utf-8") as f:
        for line in train_mem:
            f.write(line + "\n")
    with (mem_dir / "valid_mem.txt").open("w", encoding="utf-8") as f:
        for line in valid_mem:
            f.write(line + "\n")


def _predict_dataset(
    args: SimpleNamespace,
    model: T5forSummarization,
    dataset: T5SummarizationDataset,
    batch_size: int,
) -> List[str]:
    loader = _get_dataloader(
        args.num_workers,
        dataset,
        batch_size,
        args.max_length,
        SequentialSampler(dataset),
    )
    model.eval()
    preds: List[str] = []
    with torch.no_grad():
        for batch in loader:
            inputs = {
                "input_ids": batch[0].to(args.device),
                "attention_mask": batch[1].to(args.device),
                "target_ids": batch[2].to(args.device),
                "target_mask": batch[3].to(args.device),
            }
            _inp, _tgt, batch_preds = model._generative_step(inputs)
            preds.extend(batch_preds)
    return preds


def _score_examples(
    examples: Sequence[Dict[str, Any]],
    preds: Sequence[str],
    normalization_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    ems: List[float] = []
    f1s: List[float] = []
    details: List[Dict[str, Any]] = []
    for ex, pred in zip(examples, preds):
        prompt = _format_input(ex)
        gold = str(ex.get("output", "") or "")
        norm_pred = _normalize(pred or "", prompt=prompt, cfg=normalization_cfg)
        norm_gold = _normalize(gold, prompt=prompt, cfg=normalization_cfg)
        em = float(norm_pred == norm_gold)
        f1 = float(_token_f1(norm_pred, norm_gold))
        ems.append(em)
        f1s.append(f1)
        details.append(
            {
                "instruction": ex.get("instruction", ""),
                "input": ex.get("input", ""),
                "gold_output": gold,
                "prediction": pred,
                "normalized_prediction": norm_pred,
                "normalized_gold": norm_gold,
                "exact_match": bool(em),
                "token_f1": f1,
            }
        )
    n = max(1, len(ems))
    return {
        "accuracy": float(sum(ems) / n),
        "token_f1_mean": float(sum(f1s) / n),
        "num_examples": len(ems),
        "details": details,
    }


def _evaluate_seen_segments(
    *,
    args: SimpleNamespace,
    model: T5forSummarization,
    tokenizer: T5Tokenizer,
    gentasktokens: Sequence[str],
    answertoken: str,
    current_task_idx: int,
    seen_eval_examples: Sequence[Tuple[int, Sequence[Dict[str, Any]]]],
    normalization_cfg: Dict[str, Any],
    historical_best: Dict[int, float],
) -> Dict[str, Any]:
    per_seg_acc: List[Tuple[int, float]] = []
    per_seg_f1: List[Tuple[int, float]] = []
    scored_details_by_segment: List[Dict[str, Any]] = []
    all_token_f1: List[float] = []
    for seg_id, examples in seen_eval_examples:
        eval_tsv = args.work_dir / f"eval_seg_{seg_id:03d}.txt"
        _write_tsv(eval_tsv, _json_examples_to_rows(examples, seg_id))
        eval_ds = CITBT5SummarizationDataset(
            str(eval_tsv),
            args.max_length,
            tokenizer,
            list(gentasktokens),
            answertoken,
            current_task_idx,
        )
        preds = _predict_dataset(args, model, eval_ds, args.test_size_per_gpu)
        scored = _score_examples(examples, preds, normalization_cfg)
        per_seg_acc.append((seg_id, scored["accuracy"]))
        per_seg_f1.append((seg_id, scored["token_f1_mean"]))
        all_token_f1.extend([float(x["token_f1"]) for x in scored["details"]])
        scored_details_by_segment.append(
            {
                "segment_id": int(seg_id),
                "accuracy": float(scored["accuracy"]),
                "token_f1_mean": float(scored["token_f1_mean"]),
                "examples": scored["details"],
            }
        )

    current_score = float(per_seg_acc[-1][1]) if per_seg_acc else 0.0
    seen_avg_score = float(sum(a for _, a in per_seg_acc) / max(1, len(per_seg_acc)))
    forgetting_values: List[float] = []
    forgetting_by_segment: List[Dict[str, float]] = []
    previous_ids = {sid for sid, _ in per_seg_acc[:-1]}
    for sid, acc in per_seg_acc:
        best_before = float(historical_best.get(sid, acc))
        seg_forgetting = float(max(0.0, best_before - acc)) if sid in previous_ids else 0.0
        if sid in previous_ids:
            forgetting_values.append(seg_forgetting)
        forgetting_by_segment.append(
            {
                "segment_id": int(sid),
                "accuracy": float(acc),
                "best_historical_accuracy": float(best_before),
                "forgetting": float(seg_forgetting),
            }
        )
        historical_best[sid] = max(best_before, float(acc))

    forgetting = float(sum(forgetting_values) / max(1, len(forgetting_values))) if forgetting_values else 0.0
    return {
        "current_score": current_score,
        "seen_avg_score": seen_avg_score,
        "current_task_aware_score": current_score,
        "seen_avg_task_aware_score": seen_avg_score,
        "forgetting": forgetting,
        "task_aware_forgetting": forgetting,
        "num_seen_segments": len(per_seg_acc),
        "token_f1_mean": float(sum(all_token_f1) / max(1, len(all_token_f1))),
        "extra": {
            "per_segment_accuracy": [{"segment_id": sid, "accuracy": acc} for sid, acc in per_seg_acc],
            "per_segment_token_f1": [{"segment_id": sid, "token_f1_mean": f1} for sid, f1 in per_seg_f1],
            "forgetting_by_segment": forgetting_by_segment,
            "token_f1_mean": float(sum(all_token_f1) / max(1, len(all_token_f1))),
            "scored_details_by_segment": scored_details_by_segment,
        },
    }


def _flatten_metrics(prefix: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for k, v in (metrics or {}).items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            flat[f"{prefix}.{k}"] = v
    return flat


def _build_lfpt5_args(
    cfg: Dict[str, Any],
    *,
    cuda: str,
    max_epoch: int,
    work_dir: Path,
    ckpt_root: Path,
) -> SimpleNamespace:
    lfpt5_cfg = cfg.get("lfpt5") or {}
    ckpt = REPO / lfpt5_cfg.get(
        "lm_adapted_torch_ckpt",
        "assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin",
    )
    local_t5 = REPO / "assets/pretrained/hf_cache/google/t5-v1_1-large"
    default_model_name = (
        str(local_t5)
        if local_t5.is_dir() and (local_t5 / "spiece.model").is_file()
        else "google/t5-v1_1-large"
    )
    return SimpleNamespace(
        cuda=cuda,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        n_gpu=1,
        local_rank=-1,
        seed=int(cfg.get("seed", 42)),
        lr=float(lfpt5_cfg.get("lr", 5e-5)),
        lm_lambda=float(lfpt5_cfg.get("lm_lambda", 0.25)),
        kd_lamda=float(lfpt5_cfg.get("kd_lamda", 0.05)),
        batch_size_per_gpu=int(lfpt5_cfg.get("batch_size_per_gpu", 2)),
        valid_size_per_gpu=int(lfpt5_cfg.get("valid_size_per_gpu", 12)),
        test_size_per_gpu=int(lfpt5_cfg.get("test_size_per_gpu", 12)),
        gradient_accumulation_steps=int(lfpt5_cfg.get("gradient_accumulation_steps", 1)),
        max_epoch=int(max_epoch),
        num_workers=int(lfpt5_cfg.get("num_workers", 0)),
        max_length=int(lfpt5_cfg.get("max_length", 128)),
        weight_decay=float(lfpt5_cfg.get("weight_decay", 1e-5)),
        max_grad_norm=float(lfpt5_cfg.get("max_grad_norm", 1.0)),
        model_name=str(lfpt5_cfg.get("model_name", default_model_name)),
        cache_path=str(lfpt5_cfg.get("cache_path", str(REPO / "assets/pretrained/hf_cache"))),
        use_lm_adapted=1,
        lm_adapted_path=str(ckpt),
        ifckpt_onlymodel=1,
        prompt_number=int(lfpt5_cfg.get("prompt_number", 300)),
        mem_per_task=int(lfpt5_cfg.get("mem_per_task", 4)),
        work_dir=work_dir,
        ckpt_root=ckpt_root,
        tosavepath=str(ckpt_root),
    )


def run_continual(
    *,
    cfg: Dict[str, Any],
    export_dir: Path,
    run_dir: Path,
    max_segments: int,
    max_epoch: int,
    cuda: str,
) -> int:
    run_name = (cfg.get("output") or {}).get("run_name", "lfpt5_run")
    work_dir = run_dir / "lfpt5_bridge_work"
    ckpt_root = run_dir / "lfpt5_ckpt"
    work_dir.mkdir(parents=True, exist_ok=True)
    ckpt_root.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    config_snapshot = run_dir / "config_snapshot.yaml"
    config_snapshot.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    tracker = WandbTracker.from_config(
        cfg=cfg,
        run_id=run_name,
        config_path=str(config_snapshot.relative_to(REPO)),
        run_dir=str(run_dir),
    )

    segments = discover_segments(export_dir)
    if max_segments > 0:
        segments = segments[:max_segments]
    if not segments:
        logger.error("No segment_* directories under %s", export_dir)
        tracker.finish(success=False, error="no segment directories")
        return 10

    try:
        normalization_cfg = cfg.get("eval_normalization", {}) if isinstance(cfg.get("eval_normalization", {}), dict) else {}
        args = _build_lfpt5_args(cfg, cuda=cuda, max_epoch=max_epoch, work_dir=work_dir, ckpt_root=ckpt_root)
        os.environ["CUDA_VISIBLE_DEVICES"] = cuda
        if torch.cuda.is_available():
            args.device = torch.device("cuda")
        seed_everything(args)

        gentasktokens = [f"citbtask{i}" for i in range(len(segments))]
        answertoken = "__ans__"
        mem_root = work_dir / "memdata"
        classification_stream = _is_classification_stream(cfg)

        local_t5_dir = Path(args.model_name)
        tokenizer_kwargs = {"local_files_only": True} if local_t5_dir.is_dir() else {}
        tokenizer = T5Tokenizer.from_pretrained(args.model_name, cache_dir=args.cache_path, **tokenizer_kwargs)
        for token in gentasktokens:
            tokenizer.add_tokens(token)
        tokenizer.add_tokens([answertoken])
        args.blocked_generation_token_ids = [
            token_id
            for token_id in [tokenizer.convert_tokens_to_ids(token) for token in [*gentasktokens, answertoken]]
            if token_id is not None and int(token_id) >= 0
        ]
        args.answer_token_text = answertoken

        segment_metrics_rows: List[Dict[str, Any]] = []
        historical_best: Dict[int, float] = {}
        seen_eval: List[Tuple[int, List[Dict[str, Any]]]] = []

        for task_idx, (seg_id, seg_folder_name, seg_path) in enumerate(segments):
            seg_name = seg_folder_name.split("_", 2)[-1] if "_" in seg_folder_name else seg_folder_name
            train_examples = _load_json_list(seg_path / "train.json")
            eval_examples = _load_json_list(seg_path / "eval.json")
            seen_eval.append((seg_id, eval_examples))

            logger.info("=== LFPT5 segment %s (%s) task_idx=%s ===", seg_id, seg_name, task_idx)
            t5model = T5ForConditionalGeneration.from_pretrained(
                args.model_name, cache_dir=args.cache_path, **tokenizer_kwargs
            )
            model = T5forSummarization(args, t5model, tokenizer)

            if task_idx == 0:
                classification_labels = (
                    _ordered_unique_outputs([*train_examples, *eval_examples])
                    if classification_stream
                    else None
                )
                if classification_stream:
                    logger.info("LFPT5 classification labels for first segment: %s", classification_labels)
                prompt_emb = _init_prompt_embedding(
                    model,
                    tokenizer,
                    args.prompt_number,
                    seg_name,
                    classification_labels=classification_labels,
                )
                model.set_prompt_embedding(args.prompt_number, prompt_emb)
            else:
                prev_ckpt = ckpt_root / f"segment_{segments[task_idx - 1][0]:03d}" / "bestckpt"
                _load_prompt_ckpt(model, prev_ckpt, args.prompt_number)

            model.to(args.device)

            seg_work = work_dir / f"segment_{seg_id:03d}"
            seg_work.mkdir(parents=True, exist_ok=True)
            train_rows = _json_examples_to_rows(train_examples, task_idx)
            valid_rows = _json_examples_to_rows(eval_examples, task_idx)

            if task_idx > 0:
                for prev_idx in range(task_idx):
                    prev_seg_id = segments[prev_idx][0]
                    prev_eval_tsv = seg_path.parent / segments[prev_idx][1] / "eval.json"
                    pseudo_src = work_dir / f"pseudo_eval_{prev_seg_id:03d}.txt"
                    _write_tsv(pseudo_src, _json_examples_to_rows(_load_json_list(prev_eval_tsv), prev_idx))
                    _generate_pseudo_memory(
                        args,
                        model,
                        tokenizer,
                        gentasktokens,
                        answertoken,
                        task_idx,
                        pseudo_src,
                        mem_root / f"segment_{prev_seg_id:03d}",
                        args.mem_per_task,
                    )
                for prev_idx in range(task_idx):
                    prev_seg_id = segments[prev_idx][0]
                    mem_train = mem_root / f"segment_{prev_seg_id:03d}" / "train_mem.txt"
                    mem_valid = mem_root / f"segment_{prev_seg_id:03d}" / "valid_mem.txt"
                    if mem_train.is_file():
                        with mem_train.open("r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                parts = line.split("\t", 1)
                                if len(parts) == 2:
                                    train_rows.append((prev_idx, _tsv_unescape(parts[0]), _tsv_unescape(parts[1])))
                    if mem_valid.is_file():
                        with mem_valid.open("r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                parts = line.split("\t", 1)
                                if len(parts) == 2:
                                    valid_rows.append((prev_idx, _tsv_unescape(parts[0]), _tsv_unescape(parts[1])))

            train_tsv = seg_work / "train.txt"
            valid_tsv = seg_work / "valid.txt"
            _write_tsv(train_tsv, train_rows)
            _write_tsv(valid_tsv, valid_rows)

            train_ds = CITBT5SummarizationDataset(
                str(train_tsv), args.max_length, tokenizer, gentasktokens, answertoken, task_idx
            )
            train_metrics = _train_single_gpu(args, model, train_ds)

            ckpt_path = ckpt_root / f"segment_{seg_id:03d}" / "bestckpt"
            _save_prompt_ckpt(model, ckpt_path)

            eval_metrics = _evaluate_seen_segments(
                args=args,
                model=model,
                tokenizer=tokenizer,
                gentasktokens=gentasktokens,
                answertoken=answertoken,
                current_task_idx=task_idx,
                seen_eval_examples=seen_eval,
                normalization_cfg=normalization_cfg,
                historical_best=historical_best,
            )

            row = {
                "run_id": run_name,
                "mode": "baseline",
                "baseline_name": "lfpt5",
                "segment_id": seg_id,
                "segment_name": seg_name,
                **_flatten_metrics("train", train_metrics),
                **_flatten_metrics("eval", eval_metrics),
            }
            segment_metrics_rows.append(row)
            append_jsonl(str(run_dir / "metrics.jsonl"), row)
            save_json(str(run_dir / f"segment_{seg_id:03d}" / "train_metrics.json"), train_metrics)
            save_json(str(run_dir / f"segment_{seg_id:03d}" / "eval_metrics.json"), eval_metrics)
            tracker.log_segment_row(row)

            del model, t5model, train_ds
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        final_row = segment_metrics_rows[-1] if segment_metrics_rows else {}
        final_metrics = {
            "run_id": run_name,
            "mode": "baseline",
            "baseline_name": "lfpt5",
            "final": final_row,
            "drift_quality": {},
            "routing_quality": {},
        }
        final_path = run_dir / "final_metrics.json"
        table_path = REPO / "results" / "tables" / f"{run_name}_segment_metrics.csv"
        save_json(str(final_path), final_metrics)
        save_csv(str(table_path), segment_metrics_rows)
        tracker.log_final(final_metrics)
        tracker.log_artifacts([final_path, table_path, config_snapshot])
        tracker.finish(success=True)
        logger.info("Wrote final_metrics.json to %s", final_path)
        return 0
    except Exception as exc:
        tracker.finish(success=False, error=str(exc))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="LFPT5 continual bridge for CITB streams")
    parser.add_argument("--config", required=True, help="published_setting LFPT5 yaml")
    parser.add_argument("--export-dir", required=True, help="lfpt5_export directory with segment_* folders")
    parser.add_argument("--run-dir", required=True, help="results/runs/<run_name>")
    parser.add_argument("--max-segments", type=int, default=-1, help="Limit segments (-1 = all)")
    parser.add_argument("--max-epoch", type=int, default=4, help="Epochs per segment (default 4)")
    parser.add_argument("--cuda", type=str, default="0", help="CUDA_VISIBLE_DEVICES value")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = REPO / cfg_path
    export_dir = Path(args.export_dir)
    if not export_dir.is_absolute():
        export_dir = REPO / export_dir
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO / run_dir

    if not cfg_path.is_file():
        logger.error("Config missing: %s", cfg_path)
        return 2
    if not export_dir.is_dir():
        logger.error("Export dir missing: %s", export_dir)
        return 3

    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    return run_continual(
        cfg=cfg,
        export_dir=export_dir,
        run_dir=run_dir,
        max_segments=int(args.max_segments),
        max_epoch=int(args.max_epoch),
        cuda=str(args.cuda),
    )


if __name__ == "__main__":
    sys.exit(main())
