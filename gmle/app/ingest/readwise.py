"""Readwise ingest."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.http.readwise_client import fetch_highlights
from gmle.app.ingest.refine import refine_source


def ingest_readwise(space_id: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Ingest from Readwise."""
    params = params or {}
    highlights = fetch_highlights(params)
    sources = []
    for hl in highlights.get("results", []):
        raw = {
            "title": hl.get("book", {}).get("title", ""),
            "locator": hl.get("location", ""),
            "url": hl.get("url"),
            "excerpt": hl.get("text", ""),
            "domain_path": None,
        }
        refined = refine_source(raw)
        sources.extend(refined)
    return sources
