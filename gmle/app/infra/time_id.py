"""Time and ID utilities."""

from __future__ import annotations

import datetime as dt
import uuid


def today_str(date: dt.date | None = None) -> str:
    """Return YYYY-MM-DD string."""
    target = date or dt.date.today()
    return target.isoformat()


def new_run_id() -> str:
    """Generate run_id."""
    return uuid.uuid4().hex


def datestamp_and_run_id() -> tuple[str, str]:
    """Utility returning date string and run_id."""
    return today_str(), new_run_id()
