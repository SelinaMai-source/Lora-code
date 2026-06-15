#!/usr/bin/env python3
"""Queue failed tool/shell events for automatic agent follow-up.

This hook deliberately does not fail closed. It records compact diagnostics so
the agent can continue fixing issues without dumping raw errors to the user.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
QUEUE_DIR = ROOT / ".cursor" / "error-autofix"
QUEUE_PATH = QUEUE_DIR / "queue.jsonl"


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)authorization:\s*bearer\s+[a-z0-9._~+/=-]+"),
]


def _mask_secret(match: re.Match[str]) -> str:
    text = match.group(0)
    sep = "=" if "=" in text else ":"
    key = text.split(sep, 1)[0]
    return f"{key}{sep}<redacted>"


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        text = value
        for pattern in SECRET_PATTERNS:
            text = pattern.sub(_mask_secret, text)
        if len(text) > 4000:
            return text[:4000] + "\n...[truncated]"
        return text
    if isinstance(value, list):
        return [_redact(item) for item in value[:50]]
    if isinstance(value, dict):
        return {str(k): _redact(v) for k, v in list(value.items())[:80]}
    return value


def _looks_failed(payload: dict[str, Any]) -> bool:
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(key in payload for key in ("error", "exception", "failure")):
        return True
    if payload.get("status") in {"failed", "error"}:
        return True
    for key in ("exit_code", "last_exit_code", "code"):
        value = payload.get(key)
        if isinstance(value, int) and value != 0:
            return True
    return any(marker in text for marker in ("traceback", "error:", "exception", "failed", "exit code: 1"))


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception as exc:
        payload = {"hook_parse_error": repr(exc)}

    if not isinstance(payload, dict):
        payload = {"event": payload}

    if not _looks_failed(payload):
        print("{}")
        return 0

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pending",
        "summary": "A tool or shell command failed. Agent should diagnose and fix before reporting raw errors.",
        "event": _redact(payload),
    }
    with QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "additional_context": (
                    "A failure was queued for automatic handling. Do not show raw error output to the user; "
                    "diagnose, retry/fix if safe, and summarize only the actionable result."
                )
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
