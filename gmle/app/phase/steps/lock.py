"""Phase 0: Lock."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.infra.errors import InfraError
from gmle.app.infra.lock import acquire_lock


def execute(context: Dict[str, Any]) -> None:
    """Acquire lock (Phase 0)."""
    paths = context["paths"]
    try:
        acquire_lock(paths["lock"])
    except InfraError as exc:
        raise InfraError(f"lock acquisition failed: {paths['lock']}") from exc
