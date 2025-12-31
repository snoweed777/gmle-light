"""Repair command (spec 20)."""

from __future__ import annotations

import typer

from gmle.app.adapters.anki_client import build_base_query, find_notes, notes_info
from gmle.app.config.loader import load_config


def repair_cmd(space: str = typer.Option(..., "--space", help="Space ID")) -> None:
    """Repair duplicate IDs and multi-card issues (spec 20)."""
    context = load_config({"space": space})
    deck_bank = context["deck_bank"]

    query = build_base_query(deck_bank)
    base_note_ids = find_notes(query)
    notes = notes_info(base_note_ids)

    id_tags: dict[str, list[int]] = {}
    for note in notes:
        tags = note.get("tags", [])
        for tag in tags:
            if tag.startswith("id::"):
                id_val = tag[4:]
                if id_val not in id_tags:
                    id_tags[id_val] = []
                id_tags[id_val].append(note["noteId"])

    duplicates = {k: v for k, v in id_tags.items() if len(v) > 1}
    if duplicates:
        typer.echo("Duplicate IDs found:")
        for item_id, note_ids in duplicates.items():
            typer.echo(f"  {item_id}: {note_ids}")
        typer.echo("Use Anki to manually resolve duplicates")
    else:
        typer.echo("✓ No duplicate IDs")

    multi_card_notes = [n for n in notes if len(n.get("cards", [])) != 1]
    if multi_card_notes:
        typer.echo("Multi-card notes found:")
        for note in multi_card_notes:
            typer.echo(f"  Note {note['noteId']}: {len(note.get('cards', []))} cards")
        typer.echo("Fix note templates in Anki")
    else:
        typer.echo("✓ All notes have 1 card")
