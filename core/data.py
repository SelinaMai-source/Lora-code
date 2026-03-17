import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.utils import ensure_dir


@dataclass
class Example:
    instruction: str
    input: str
    output: str


@dataclass
class Segment:
    segment_id: int
    segment_name: str
    train: List[Example]
    eval: List[Example]


@dataclass
class ContinualStream:
    benchmark: str
    version: str
    stream: List[Segment]


def _parse_example(obj: Dict[str, Any]) -> Example:
    for k in ["instruction", "input", "output"]:
        if k not in obj:
            raise ValueError(f"Example missing key '{k}': {obj}")
    return Example(
        instruction=str(obj["instruction"]),
        input=str(obj.get("input", "")),
        output=str(obj["output"]),
    )


def _parse_stream_json(path: str) -> ContinualStream:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if "stream" not in raw or not isinstance(raw["stream"], list):
        raise ValueError(f"Invalid stream json: missing list field 'stream' in {path}")

    segments: List[Segment] = []
    for seg in raw["stream"]:
        if "segment_id" not in seg:
            raise ValueError(f"Segment missing 'segment_id': {seg}")
        if "segment_name" not in seg:
            raise ValueError(f"Segment missing 'segment_name': {seg}")
        train = [_parse_example(x) for x in seg.get("train", [])]
        ev = [_parse_example(x) for x in seg.get("eval", [])]
        if not train or not ev:
            raise ValueError(
                f"Each segment must include non-empty train & eval lists. Bad segment: {seg.get('segment_id')}"
            )
        segments.append(
            Segment(
                segment_id=int(seg["segment_id"]),
                segment_name=str(seg["segment_name"]),
                train=train,
                eval=ev,
            )
        )

    return ContinualStream(
        benchmark=str(raw.get("benchmark", "unknown")),
        version=str(raw.get("version", "unknown")),
        stream=segments,
    )


def load_continual_stream(
    *,
    mode: str,
    sample_stream_path: Optional[str],
    processed_stream_dir: Optional[str],
    processed_stream_file: str = "",
    max_segments: int = -1,
    max_train_examples_per_segment: int = -1,
    max_eval_examples_per_segment: int = -1,
) -> ContinualStream:
    """
    Unified stream loader.

    - debug 模式：读取 data/sample/mock_stream.json
    - baseline/ours：读取 data/processed 下的 CITB 处理后流式文件（JSON）
    """

    if mode == "debug":
        if not sample_stream_path:
            raise ValueError("debug mode requires sample_stream_path")
        stream = _parse_stream_json(sample_stream_path)
    else:
        if not processed_stream_dir:
            raise ValueError("baseline/ours mode requires processed_stream_dir")
        stream_path = resolve_processed_stream_path(processed_stream_dir, processed_stream_file)
        stream = _parse_stream_json(stream_path)

    stream = truncate_stream(
        stream,
        max_segments=max_segments,
        max_train_examples_per_segment=max_train_examples_per_segment,
        max_eval_examples_per_segment=max_eval_examples_per_segment,
    )
    return stream


def truncate_stream(
    stream: ContinualStream,
    *,
    max_segments: int,
    max_train_examples_per_segment: int,
    max_eval_examples_per_segment: int,
) -> ContinualStream:
    segments = stream.stream
    if max_segments is not None and max_segments > 0:
        segments = segments[: max_segments]

    new_segments: List[Segment] = []
    for seg in segments:
        tr = seg.train
        ev = seg.eval
        if max_train_examples_per_segment is not None and max_train_examples_per_segment > 0:
            tr = tr[: max_train_examples_per_segment]
        if max_eval_examples_per_segment is not None and max_eval_examples_per_segment > 0:
            ev = ev[: max_eval_examples_per_segment]
        new_segments.append(
            Segment(segment_id=seg.segment_id, segment_name=seg.segment_name, train=tr, eval=ev)
        )

    return ContinualStream(benchmark=stream.benchmark, version=stream.version, stream=new_segments)


def resolve_processed_stream_path(processed_stream_dir: str, processed_stream_file: str = "") -> str:
    """
    Find a processed stream json path.

    - If processed_stream_file is provided, use it (relative to processed_stream_dir if not absolute)
    - Otherwise, try to auto-detect a single *.json file inside processed_stream_dir
    """

    d = Path(processed_stream_dir)
    if not d.exists():
        raise FileNotFoundError(
            f"Processed data directory not found: {processed_stream_dir}. "
            f"Please generate processed stream under data/processed/."
        )

    if processed_stream_file:
        p = Path(processed_stream_file)
        if not p.is_absolute():
            p = d / p
        if not p.exists():
            raise FileNotFoundError(f"Processed stream file not found: {str(p)}")
        return str(p)

    candidates = sorted(list(d.glob("*.json")))
    if len(candidates) == 1:
        return str(candidates[0])
    if len(candidates) == 0:
        raise FileNotFoundError(
            f"No processed stream json found in {processed_stream_dir}. "
            f"Expected a single *.json. See data/processed/README.md."
        )
    raise FileExistsError(
        f"Multiple processed stream json files found in {processed_stream_dir}: "
        f"{[c.name for c in candidates]}. Please set processed_stream_file in config."
    )


def preprocess_citb_raw_to_processed(
    raw_root: str,
    processed_out_path: str,
    *,
    benchmark_name: str = "CITB",
    version: str = "unknown",
) -> None:
    """
    Preprocessing scaffold (NOT a fake implementation).

    This function is the intended extension point to convert raw CITB data in
    data/raw/citb/ into the unified continual stream JSON format under data/processed/.

    Current behavior:
      - validates input directories exist
      - creates output directory
      - raises an informative error describing what to implement

    Why keep it here?
      - Repo structure constraint: preprocessing logic must live in core/data.py.
    """

    raw_root_p = Path(raw_root)
    if not raw_root_p.exists():
        raise FileNotFoundError(
            f"Raw CITB root not found: {raw_root}. "
            f"Place raw data under data/raw/citb/ (see data/raw/README.md)."
        )

    ensure_dir(str(Path(processed_out_path).parent))

    raise NotImplementedError(
        "CITB preprocessing is intentionally not implemented because the exact raw file "
        "layout depends on how you obtained CITB. Implement parsing here:\n"
        f"- Input raw_root: {raw_root}\n"
        f"- Output processed_out_path: {processed_out_path}\n"
        "Expected output format is described in data/processed/README.md.\n"
        "Tip: map CITB tasks/domains to segment_id order, and create per-segment train/eval lists."
    )

