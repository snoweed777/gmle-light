"""Lint queue command."""

from __future__ import annotations

import typer

from gmle.app.config.loader import load_config


def lint_queue_cmd(space: str = typer.Option(..., "--space", help="Space ID")) -> None:
    """Lint queue.jsonl."""
    context = load_config({"space": space})
    queue_path = context["paths"]["queue"]

    if not queue_path.exists():
        typer.echo("queue.jsonl not found")
        return

    import orjson
    errors = []
    with queue_path.open("rb") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = orjson.loads(line)
                if "source_id" not in data:
                    errors.append(f"Line {line_num}: missing source_id")
                if "excerpt" not in data:
                    errors.append(f"Line {line_num}: missing excerpt")
                excerpt_len = len(data.get("excerpt", ""))
                if excerpt_len < 200 or excerpt_len > 800:
                    errors.append(f"Line {line_num}: excerpt length {excerpt_len} (200-800 required)")
            except Exception as exc:
                errors.append(f"Line {line_num}: parse error: {exc}")

    if errors:
        for err in errors:
            typer.echo(f"✗ {err}")
    else:
        typer.echo("✓ queue.jsonl valid")
