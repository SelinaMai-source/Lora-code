#!/usr/bin/env python3
"""Ask the agent to continue when queued failures are still pending."""

from __future__ import annotations

import json
import sys
from pathlib import Path


QUEUE_PATH = Path.cwd() / ".cursor" / "error-autofix" / "queue.jsonl"


def _pending_count() -> int:
    if not QUEUE_PATH.exists():
        return 0
    count = 0
    for line in QUEUE_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            record = json.loads(line)
        except Exception:
            continue
        if record.get("status", "pending") == "pending":
            count += 1
    return count


def main() -> int:
    _ = sys.stdin.read()
    count = _pending_count()
    if count <= 0:
        print("{}")
        return 0

    print(
        json.dumps(
            {
                "followup_message": (
                    f"There are {count} queued failure event(s). Continue diagnosing and fixing them automatically. "
                    "Do not paste raw error output to the user. If a failure requires user input, summarize the blocker "
                    "briefly and ask for the specific decision needed."
                )
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
