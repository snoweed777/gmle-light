"""AnkiConnect connectivity check."""

from __future__ import annotations

from gmle.app.adapters.anki_client import invoke
from gmle.app.infra.errors import AnkiError


def check_anki_connect() -> None:
    """Check AnkiConnect connectivity (version)."""
    try:
        version = invoke("version")
        if not isinstance(version, int):
            raise AnkiError(f"version returned non-int: {type(version)}")
    except Exception as exc:
        raise AnkiError("anki connect unavailable") from exc
