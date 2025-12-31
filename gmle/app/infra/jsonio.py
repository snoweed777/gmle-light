"""JSON IO helpers with atomic write."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import orjson

from .errors import InfraError


def read_json(path: Path) -> Any:
    """Read JSON file."""
    try:
        with path.open("rb") as f:
            return orjson.loads(f.read())
    except FileNotFoundError:
        raise
    except Exception as exc:  # pragma: no cover - safety net
        raise InfraError(f"failed to read json: {path}") from exc


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON file atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with open(tmp_fd, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
        Path(tmp_path).replace(path)
    except Exception as exc:  # pragma: no cover - safety net
        raise InfraError(f"failed to write json atomically: {path}") from exc
    finally:
        try:
            if Path(tmp_path).exists():
                Path(tmp_path).unlink(missing_ok=True)
        except OSError:
            pass
