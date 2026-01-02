"""Source refinement (spec 21.2)."""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Any, Dict, List

from gmle.app.config.getter import get_ingest_config


def refine_source(raw: Dict[str, Any], config: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Refine source into queue entries (spec 21.2)."""
    ingest_config = get_ingest_config(config)
    excerpt_min = ingest_config["excerpt_min"]
    excerpt_max = ingest_config["excerpt_max"]
    
    excerpt = _normalize_excerpt(raw.get("excerpt", ""))
    if not excerpt:
        return []

    excerpts = _split_excerpt(excerpt, excerpt_min=excerpt_min, excerpt_max=excerpt_max)
    if not excerpts:
        return []

    results = []
    for exc in excerpts:
        source_id = _generate_source_id(raw.get("url", ""), raw.get("locator", ""), exc)
        domain_path = raw.get("domain_path") or "unknown/unknown/unknown"
        locator = raw.get("locator") or ("unknown" if raw.get("url") else None)

        if not locator:
            return []  # quarantine

        results.append({
            "source_id": source_id,
            "title": raw.get("title", ""),
            "locator": locator,
            "url": raw.get("url"),
            "excerpt": exc,
            "domain_path": domain_path,
        })
    return results


def _normalize_excerpt(text: str) -> str:
    """NFKC normalization."""
    return unicodedata.normalize("NFKC", text).strip()


def _split_excerpt(text: str, excerpt_min: int = 200, excerpt_max: int = 650) -> List[str]:
    """Split/combine to excerpt_min-excerpt_max chars, 1論点化 (spec 21.2).
    
    Improved to strictly enforce excerpt_max limit with safety margin.
    """
    if excerpt_min <= len(text) <= excerpt_max:
        return [text]
    if len(text) < excerpt_min:
        return []  # Too short, will be quarantined
    
    chunks = []
    current = ""
    
    # Split by Japanese sentence delimiter
    for sentence in text.split("。"):
        if not sentence.strip():
            continue
        test_chunk = current + sentence + "。" if current else sentence + "。"
        
        # Strictly enforce excerpt_max limit
        if len(test_chunk) <= excerpt_max:
            current = test_chunk
        else:
            # Save current chunk if it meets minimum requirement
            if current and len(current) >= excerpt_min:
                chunks.append(current)
            
            # Handle single sentence that's too long
            if len(sentence) > excerpt_max:
                # Force split long sentence into excerpt_max chunks
                sentence_with_period = sentence + "。"
                for i in range(0, len(sentence_with_period), excerpt_max):
                    chunk = sentence_with_period[i:i+excerpt_max]
                    if len(chunk) >= excerpt_min:
                        chunks.append(chunk)
                current = ""
            else:
                current = sentence + "。"
    
    # Handle remaining text
    if current and len(current) >= excerpt_min:
        if len(current) <= excerpt_max:
            chunks.append(current)
        else:
            # Force truncate if over max
            chunks.append(current[:excerpt_max])
    elif current and len(chunks) > 0:
        # Try to merge with last chunk if it won't exceed max
        if len(chunks[-1] + current) <= excerpt_max:
            chunks[-1] = chunks[-1] + current
        else:
            # Truncate and add as separate chunk if meets minimum
            if len(current) >= excerpt_min:
                chunks.append(current[:excerpt_max])
    
    # Fallback: if no chunks created, force split the text
    if not chunks and len(text) >= excerpt_min:
        chunks = [text[:excerpt_max]]
    
    return chunks


def _generate_source_id(url: str, locator: str, excerpt: str) -> str:
    """Generate stable source_id (spec 21.3)."""
    combined = f"{url}|{locator}|{excerpt}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
