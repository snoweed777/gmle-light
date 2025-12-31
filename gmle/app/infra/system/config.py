"""GMLE Light プロセス管理設定

PIDファイルパスとサービス設定を定義します。
※ Anki/AnkiConnectはローカルMacで管理（Docker外）
"""

from __future__ import annotations

from typing import Dict, TypedDict


class ServiceConfig(TypedDict, total=False):
    """サービス設定の型定義"""
    port: int
    health_check: str
    script: str | None
    process_pattern: str
    start_timeout: int


# PIDファイルパス
PID_FILES: Dict[str, str] = {
    "api": "/tmp/gmle-api.pid",
    "gui": "/tmp/gmle-gui.pid",
}

# サービス設定
SERVICES: Dict[str, ServiceConfig] = {
    "anki": {
        # ローカルMacのAnkiConnect（Docker外）
        "port": 8765,
        "health_check": "http://host.docker.internal:8765",
        "script": None,  # ローカルで管理
        "process_pattern": "anki",
        "start_timeout": 5,
    },
    "api": {
        "port": 8000,
        "health_check": "http://localhost:8000/health",
        "script": "start_api.sh",
        "process_pattern": "uvicorn.*gmle.app.api.rest.main",
        "start_timeout": 10,
    },
    "gui": {
        "port": 3001,
        "health_check": "http://localhost:3001",
        "script": None,
        "process_pattern": "vite",
        "start_timeout": 15,
    },
}
