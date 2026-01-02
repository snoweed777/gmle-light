"""MCQ Generator (spec 15)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.infra.errors import InfraError
from .gates import hard_gate, soft_gate
from .stage1_extract import extract_facts_relations
from .stage2_build_mcq import build_mcq


def generate_mcq(source: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Generate MCQ from source (spec 15)."""
    from gmle.app.infra.logger import get_logger, with_fields
    logger = get_logger()
    
    excerpt = source["excerpt"]
    source_id = source.get("source_id", "unknown")
    
    try:
        # Stage 1: Extract facts and relations
        extracted = extract_facts_relations(excerpt, config=config)
        facts = extracted.get("facts", [])
        relations = extracted.get("relations", [])
        
        if not facts and not relations:
            logger.warning("Stage 1 returned no facts or relations", **with_fields(logger,
                source_id=source_id,
                excerpt_length=len(excerpt),
            ))
            return None
        
        logger.debug("Stage 1 completed", **with_fields(logger,
            source_id=source_id,
            facts_count=len(facts),
            relations_count=len(relations),
        ))
        
        # Stage 2: Build MCQ
        mcq_data = build_mcq(facts, relations, excerpt, config=config)
        
        if not mcq_data:
            logger.warning("Stage 2 returned empty MCQ data", **with_fields(logger,
                source_id=source_id,
            ))
            return None
        
        logger.debug("Stage 2 completed", **with_fields(logger,
            source_id=source_id,
            mcq_data_keys=list(mcq_data.keys()),
        ))
        
        # Hard gate validation
        passed, reason = hard_gate(mcq_data, excerpt)
        if not passed:
            logger.warning("Hard gate failed", **with_fields(logger,
                source_id=source_id,
                reason=reason,
                question_preview=mcq_data.get("question", "")[:50],
            ))
            return None
        soft_pass = soft_gate(mcq_data)
        
        # Safe field access with defaults
        item = {
            "id": f"gmle::{source['source_id']}",
            "source_id": source["source_id"],
            "domain_path": source["domain_path"],
            "format": mcq_data.get("format", "F"),
            "depth": mcq_data.get("depth", 1),
            "question": mcq_data.get("question", ""),
            "choices": mcq_data.get("choices", []),
            "answer": mcq_data.get("answer", ""),
            "rationale": mcq_data.get("rationale", {"quote": "", "text": ""}),
            "source": {
                "title": source["title"],
                "locator": source["locator"],
                "url": source.get("url"),
            },
            "meta": {
                "type_reason": "generated",
                "depth_reason": "generated",
                "facts_used": [f["id"] for f in facts],
                "relations_used": [r["id"] for r in relations],
            },
            "retired": False,
        }
        if not soft_pass:
            item["tags"] = ["qc::soft_fail"]
            logger.debug("Soft gate failed, tagged as qc::soft_fail", **with_fields(logger,
                source_id=source_id,
            ))
        
        logger.info("MCQ generation successful", **with_fields(logger,
            source_id=source_id,
            soft_pass=soft_pass,
        ))
        return item
    except Exception as exc:
        logger.error("MCQ generation exception", **with_fields(logger,
            source_id=source_id,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            excerpt_length=len(excerpt),
        ))
        raise InfraError(f"MCQ generation failed: {source['source_id']}") from exc
