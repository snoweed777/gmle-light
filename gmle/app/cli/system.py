"""GMLE+ システム管理CLI

サービスの起動・停止・状態確認を行います。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from gmle.app.infra.system import (
    get_all_status,
    get_service_status,
    start_service,
    stop_service,
)

app = typer.Typer(help="System service management")


def _get_scripts_dir() -> Path:
    """scripts/service ディレクトリのパスを取得"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    return project_root / "scripts" / "service"


@app.command()
def status(
    service: Optional[str] = typer.Argument(None, help="Service name (optional)")
) -> None:
    """Get service status."""
    if service:
        result = get_service_status(service)
        typer.echo(json.dumps(result, indent=2))
    else:
        result = get_all_status()
        typer.echo(json.dumps(result, indent=2))


@app.command()
def start(service: str = typer.Argument(..., help="Service name")) -> None:
    """Start a service."""
    scripts_dir = _get_scripts_dir()
    result = start_service(service, scripts_dir=scripts_dir)
    typer.echo(json.dumps(result, indent=2))
    if result.get("status") == "error":
        raise typer.Exit(1)


@app.command()
def stop(service: str = typer.Argument(..., help="Service name")) -> None:
    """Stop a service."""
    result = stop_service(service)
    typer.echo(json.dumps(result, indent=2))
    if result.get("status") == "error":
        raise typer.Exit(1)


@app.command()
def restart(service: str = typer.Argument(..., help="Service name")) -> None:
    """Restart a service (stop then start)."""
    scripts_dir = _get_scripts_dir()
    # まず停止
    stop_result = stop_service(service)
    if stop_result.get("status") == "error":
        typer.echo(json.dumps(stop_result, indent=2))
        raise typer.Exit(1)
    
    # 少し待機してから起動
    import time
    time.sleep(2)
    
    # 起動
    start_result = start_service(service, scripts_dir=scripts_dir)
    typer.echo(json.dumps(start_result, indent=2))
    if start_result.get("status") == "error":
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

