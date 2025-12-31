"""Audit command."""

from __future__ import annotations

import typer

from gmle.app.config.loader import load_config
from gmle.app.sot.items_io import read_items
from gmle.app.sot.validate import validate_items


def audit_cmd(space: str = typer.Option(..., "--space", help="Space ID")) -> None:
    """Audit space data."""
    context = load_config({"space": space})
    paths = context["paths"]

    if paths["items"].exists():
        items = read_items(paths["items"])
        try:
            validate_items(items)
            typer.echo(f"✓ items.json valid: {len(items)} items")
        except Exception as exc:
            typer.echo(f"✗ items.json invalid: {exc}")
    else:
        typer.echo("items.json not found")

    if paths["ledger"].exists():
        from gmle.app.sot.ledger_io import read_ledger
        ledger = read_ledger(paths["ledger"])
        typer.echo(f"✓ ledger: {len(ledger)} records")
    else:
        typer.echo("ledger not found")
