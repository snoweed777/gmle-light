"""Init command."""

from __future__ import annotations

from pathlib import Path

import typer

from gmle.app.adapters.anki_client import (
    create_deck,
    create_model,
    deck_names,
    model_names,
)
from gmle.app.config.loader import load_config
from gmle.app.infra.errors import AnkiError, InfraError


NOTE_TYPE_NAME = "GMLE_MCQA"


def init_cmd(space: str = typer.Option(..., "--space", help="Space ID")) -> None:
    """Initialize space directories and Anki resources."""
    # Load config to get deck_bank
    try:
        context = load_config({"space": space})
        deck_bank = context["deck_bank"]
    except Exception:
        deck_bank = f"GMLE::Bank::{space}"

    # Create directories
    data_dir = Path(f"data/{space}")
    sources_dir = Path(f"sources/{space}")
    data_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "runs").mkdir(exist_ok=True)
    (sources_dir / "ingest_log").mkdir(exist_ok=True)
    typer.echo(f"Initialized directories for space: {space}")

    # Create Note Type if not exists
    try:
        existing_models = model_names()
        if NOTE_TYPE_NAME not in existing_models:
            typer.echo(f"Creating Note Type: {NOTE_TYPE_NAME}")
            create_model(NOTE_TYPE_NAME)
            typer.echo(f"✅ Created Note Type: {NOTE_TYPE_NAME}")
        else:
            typer.echo(f"✅ Note Type already exists: {NOTE_TYPE_NAME}")
    except (AnkiError, InfraError) as exc:
        typer.echo(f"⚠️  Could not create Note Type: {exc}", err=True)
        typer.echo("   Please create it manually in Anki", err=True)

    # Create Deck if not exists
    try:
        existing_decks = deck_names()
        if deck_bank not in existing_decks:
            typer.echo(f"Creating Deck: {deck_bank}")
            create_deck(deck_bank)
            typer.echo(f"✅ Created Deck: {deck_bank}")
        else:
            typer.echo(f"✅ Deck already exists: {deck_bank}")
    except (AnkiError, InfraError) as exc:
        typer.echo(f"⚠️  Could not create Deck: {exc}", err=True)
        typer.echo("   Please create it manually in Anki", err=True)
