"""Items-related endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Query

from gmle.app.api.rest.errors import raise_not_found
from gmle.app.api.rest.models import ItemResponse
from gmle.app.config.loader import load_config
from gmle.app.sot.items_io import read_items

router = APIRouter(prefix="/spaces/{space_id}/items", tags=["items"])


@router.get("", response_model=List[ItemResponse])
async def list_items(
    space_id: str,
    retired: bool | None = Query(None, description="Filter by retired status"),
) -> List[ItemResponse]:
    """List items."""
    try:
        config = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)

    items_path = Path(config["paths"]["items"])
    if not items_path.exists():
        return []

    items = read_items(items_path)

    # Filter by retired status if specified
    if retired is not None:
        items = [item for item in items if item.get("retired", False) == retired]

    return [ItemResponse(**item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(space_id: str, item_id: str) -> ItemResponse:
    """Get item by ID."""
    try:
        config = load_config({"space": space_id})
    except Exception:
        raise_not_found("Space", space_id)

    items_path = Path(config["paths"]["items"])
    if not items_path.exists():
        raise_not_found("Item", item_id)

    items = read_items(items_path)
    for item in items:
        if item.get("id") == item_id:
            return ItemResponse(**item)

    raise_not_found("Item", item_id)

