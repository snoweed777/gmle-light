"""File lock handling (simple, with stale detection)."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict

from gmle.app.config.getter import get_lock_config
from .errors import InfraError


def acquire_lock(lock_path: Path, *, stale_seconds: int | None = None, config: Dict[str, Any] | None = None) -> None:
    """Acquire file lock with stale detection."""
    if stale_seconds is None:
        lock_config = get_lock_config(config)
        stale_seconds = lock_config["stale_seconds"]
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    if lock_path.exists():
        try:
            mtime = int(lock_path.stat().st_mtime)
        except OSError as exc:  # pragma: no cover
            raise InfraError(f"cannot stat lock: {lock_path}") from exc
        if now - mtime < stale_seconds:
            raise InfraError(f"lock exists and is fresh: {lock_path}")
        try:
            lock_path.unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover
            raise InfraError(f"failed to remove stale lock: {lock_path}") from exc
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        raise InfraError(f"lock already acquired: {lock_path}")
    except OSError as exc:  # pragma: no cover
        raise InfraError(f"failed to create lock: {lock_path}") from exc


def release_lock(lock_path: Path) -> None:
    """Release file lock."""
    try:
        lock_path.unlink(missing_ok=True)
    except OSError as exc:  # pragma: no cover
        raise InfraError(f"failed to release lock: {lock_path}") from exc
