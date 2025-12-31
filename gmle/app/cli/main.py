"""CLI entrypoint."""

from __future__ import annotations

import typer

from gmle.app.phase.runner import run
from gmle.app.phase.steps.selfcheck_start import execute as selfcheck_start
from gmle.app.config.loader import load_config
from .init import init_cmd
from .ingest import ingest_cmd
from .system import app as system_app

app = typer.Typer(help="GMLE+ CLI")
app.add_typer(system_app, name="system", help="System service management")


@app.command()
def run_cmd(space: str = typer.Option(None, "--space", help="Space ID")) -> None:
    """Run GMLE+ main flow."""
    if not space:
        raise typer.BadParameter("--space is required")
    run(space)


@app.command()
def batch(n: int = typer.Option(..., "--batch", help="Batch count"), space: str = typer.Option(None, "--space", help="Space ID")) -> None:
    """Run batch mode."""
    if not space:
        raise typer.BadParameter("--space is required")
    for _ in range(n):
        run(space, {"mode": "batch"})


@app.command()
def selfcheck(space: str = typer.Option(None, "--space", help="Space ID")) -> None:
    """Run selfcheck (no destructive operations)."""
    if not space:
        raise typer.BadParameter("--space is required")
    context = load_config({"space": space})
    selfcheck_start(context)


@app.command()
def init(space: str = typer.Option(..., "--space", help="Space ID")) -> None:
    """Initialize space directories."""
    init_cmd(space)


@app.command()
def ingest(
    source: str = typer.Option(..., "--from", help="Source: readwise or textfile"),
    space: str = typer.Option(..., "--space", help="Space ID"),
    input_file: str = typer.Option(None, "--input", help="Input file path"),
) -> None:
    """Ingest sources."""
    ingest_cmd(source, space, input_file)


@app.command(name="list-spaces")
def list_spaces() -> None:
    """List available spaces."""
    from pathlib import Path
    spaces_dir = Path("config/spaces")
    if not spaces_dir.exists():
        typer.echo("No spaces found")
        return
    for yaml_file in spaces_dir.glob("*.yaml"):
        typer.echo(yaml_file.stem)


if __name__ == "__main__":
    app()
