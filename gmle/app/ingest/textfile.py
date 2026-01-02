"""Text file ingest."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from gmle.app.ingest.refine import refine_source


def ingest_textfile(file_path: str, title: str | None = None, config: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Ingest from text file or docx (spec 21)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_title = title or path.stem
    content = _extract_text(path)

    raw = {
        "title": file_title,
        "locator": f"file:{path.name}",
        "url": None,
        "excerpt": content,
        "domain_path": None,
    }

    refined = refine_source(raw, config=config)
    return refined


def _extract_text(path: Path) -> str:
    """Extract text from file (supports .txt and .docx)."""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            raise ImportError("python-docx is required for .docx files: pip install python-docx")
    else:
        return path.read_text(encoding="utf-8")

