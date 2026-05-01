"""Structured JSON-line logging helpers."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.security import scrub_value


class JsonlLogger:
    """Small append-only JSONL logger scoped to a single file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def event(self, event: str, **fields: Any) -> None:
        payload = {
            "event": event,
            "ts": datetime.now(UTC).isoformat(),
            **scrub_value(fields),
        }
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def get_run_logger(run_dir: str | Path, name: str) -> JsonlLogger:
    """Return a logger at `<run_dir>/logs/<name>.log`."""

    return JsonlLogger(Path(run_dir) / "logs" / f"{name}.log")
