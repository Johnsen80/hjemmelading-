"""Utility helpers for shipping research payloads to a remote endpoint or log file."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib import request

__all__ = ["default_transport"]


def _default_log_dir() -> Path:
    """Best-effort resolution of a writable log directory."""
    try:
        from HjemmeladingApp.main import get_log_dir  # type: ignore

        return Path(get_log_dir())
    except Exception:
        return Path(os.getcwd()) / "tools" / "logs"


def default_transport(payload: Dict[str, Any]) -> None:
    """Send *payload* to remote research endpoint or persist to log file.

    The endpoint can be configured via the ``RESEARCH_ENDPOINT`` environment
    variable. When unset, payloads are appended to ``research_payloads.jsonl``
    inside the per-user log directory so they can be inspected or uploaded
    later. Any network errors are surfaced to the caller so the outbox entry
    can be retried.
    """

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    endpoint = os.environ.get("RESEARCH_ENDPOINT")

    if endpoint:
        req = request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(
            req, timeout=float(os.environ.get("RESEARCH_TIMEOUT", "10"))
        ) as resp:
            # Drain the response body so persistent HTTP servers can reuse the
            # connection if needed. The content itself is ignored.
            resp.read()
        return

    log_dir = Path(os.environ.get("RESEARCH_LOG_DIR", "")) or _default_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "research_payloads.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
