"""Ingest command."""

from __future__ import annotations

import typer

from gmle.app.api.internal.ingest_api import get_ingest_api
from gmle.app.config.loader import load_config
from gmle.app.infra.time_id import today_str
from gmle.app.ingest.writer import write_ingest_log, write_queue


def ingest_cmd(
    source: str = typer.Option(..., "--from", help="Source: readwise or textfile"),
    space: str = typer.Option(..., "--space", help="Space ID"),
    input_file: str = typer.Option(None, "--input", help="Input file path"),
) -> None:
    """Ingest sources."""
    context = load_config({"space": space})
    paths = context["paths"]
    date_str = today_str()
    
    # Get ingest API instance
    ingest_api = get_ingest_api(config=context)

    if source == "readwise":
        sources = ingest_api.ingest_readwise(space)
    elif source == "textfile":
        if not input_file:
            raise typer.BadParameter("--input is required for textfile source")
        sources = ingest_api.ingest_textfile(input_file)
    else:
        raise typer.BadParameter(f"Unknown source: {source}")

    new_sources = write_queue(paths["queue"], sources)
    write_ingest_log(paths["ingest_log_dir"], date_str, {
        "date": date_str,
        "source": source,
        "sources_count": len(sources),
        "new_sources_count": len(new_sources),
    })
    typer.echo(f"Ingested {len(new_sources)} new sources")
