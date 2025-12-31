"""JSONL (JSON Lines) file I/O utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import orjson

from gmle.app.infra.errors import InfraError
from gmle.app.infra.logger import get_logger, log_exception


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL file (one JSON object per line).
    
    Args:
        path: Path to JSONL file
        
    Returns:
        List of parsed JSON objects
        
    Raises:
        InfraError: If reading fails
    """
    if not path.exists():
        return []
    
    logger = get_logger()
    records = []
    
    try:
        with path.open("rb") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(orjson.loads(line))
                except orjson.JSONDecodeError:
                    logger.warning(
                        f"Failed to parse JSONL line {line_num}",
                        extra={
                            "extra_fields": {
                                "path": str(path),
                                "line_num": line_num,
                                "line_preview": line[:100] if len(line) > 100 else line,
                            }
                        },
                    )
                    # Continue reading other lines
                    continue
    except Exception as exc:
        log_exception(
            logger,
            f"Failed to read JSONL file: {path}",
            exc,
        )
        raise InfraError(f"Failed to read JSONL file: {path}") from exc
    
    return records


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """Append a single record to JSONL file.
    
    Args:
        path: Path to JSONL file
        record: Record to append
        
    Raises:
        InfraError: If writing fails
    """
    logger = get_logger()
    
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with path.open("ab") as f:
            f.write(orjson.dumps(record) + b"\n")
    except Exception as exc:
        log_exception(
            logger,
            f"Failed to append to JSONL file: {path}",
            exc,
        )
        raise InfraError(f"Failed to append to JSONL file: {path}") from exc


def write_jsonl(path: Path, records: List[Dict[str, Any]], append: bool = False) -> None:
    """Write records to JSONL file.
    
    Args:
        path: Path to JSONL file
        records: List of records to write
        append: If True, append to existing file; otherwise overwrite
        
    Raises:
        InfraError: If writing fails
    """
    logger = get_logger()
    
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "ab" if append else "wb"
        with path.open(mode) as f:
            for record in records:
                f.write(orjson.dumps(record) + b"\n")
        
        logger.debug(
            f"Wrote {len(records)} records to JSONL file",
            extra={
                "extra_fields": {
                    "path": str(path),
                    "record_count": len(records),
                    "append": append,
                }
            },
        )
    except Exception as exc:
        log_exception(
            logger,
            f"Failed to write JSONL file: {path}",
            exc,
        )
        raise InfraError(f"Failed to write JSONL file: {path}") from exc


def get_jsonl_ids(path: Path, id_key: str = "id") -> set[str]:
    """Get set of IDs from JSONL file.
    
    Args:
        path: Path to JSONL file
        id_key: Key to extract ID from each record
        
    Returns:
        Set of IDs
    """
    if not path.exists():
        return set()
    
    records = read_jsonl(path)
    return {str(record.get(id_key, "")) for record in records if record.get(id_key)}

