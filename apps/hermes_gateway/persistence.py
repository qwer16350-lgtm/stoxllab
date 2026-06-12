"""Local persistence helpers for dry-run Hermes Gateway logs."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_MARKERS = (
    "token",
    "password",
    "api_key",
    "api key",
    "apikey",
    "secret",
    "authorization",
    "bearer",
    "private_key",
    "private key",
    "access_key",
    "access key",
    "refresh_token",
    "refresh token",
)
REDACTED = "[REDACTED]"


def get_default_log_root(root: str | Path) -> Path:
    return Path(root) / "logs" / "hermes_gateway"


def ensure_log_dirs(log_root: str | Path) -> dict[str, Path]:
    root = Path(log_root)
    dirs = {
        "root": root,
        "replay_runs": root / "replay_runs",
        "approval_decisions": root / "approval_decisions",
        "audit_events": root / "audit_events",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def _contains_sensitive_marker(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in SENSITIVE_MARKERS)


def _is_sensitive_key(key: str) -> bool:
    return _contains_sensitive_marker(key.replace("-", "_"))


def redact_sensitive_values(payload: Any) -> Any:
    data = deepcopy(payload)
    if isinstance(data, dict):
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if _is_sensitive_key(str(key)):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_sensitive_values(value)
        return redacted
    if isinstance(data, list):
        return [redact_sensitive_values(item) for item in data]
    if isinstance(data, str):
        return REDACTED if _contains_sensitive_marker(data) else data
    return data


def write_json(path: str | Path, payload: Any, overwrite: bool = False) -> Path:
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing log file: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_payload = redact_sensitive_values(payload)
    target.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def append_jsonl(path: str | Path, payload: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_payload = redact_sensitive_values(payload)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(safe_payload, ensure_ascii=False, sort_keys=True) + "\n")
    return target


def make_timestamped_filename(prefix: str, suffix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return f"{prefix}_{stamp}{clean_suffix}"
