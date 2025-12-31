"""MCQ Generator (spec 15)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.infra.errors import InfraError
from .gates import hard_gate, soft_gate
from .stage1_extract import extract_facts_relations
from .stage2_build_mcq import build_mcq


def generate_mcq(source: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Generate MCQ from source (spec 15)."""
    excerpt = source["excerpt"]
    try:
        extracted = extract_facts_relations(excerpt, config=config)
        facts = extracted.get("facts", [])
        relations = extracted.get("relations", [])
        if not facts and not relations:
            return None
        mcq_data = build_mcq(facts, relations, excerpt, config=config)
        passed, reason = hard_gate(mcq_data, excerpt)
        if not passed:
            return None
        soft_pass = soft_gate(mcq_data)
        item = {
            "id": f"gmle::{source['source_id']}",
            "source_id": source["source_id"],
            "domain_path": source["domain_path"],
            "format": mcq_data.get("format", "F"),
            "depth": mcq_data.get("depth", 1),
            "question": mcq_data["question"],
            "choices": mcq_data["choices"],
            "answer": mcq_data["answer"],
            "rationale": mcq_data["rationale"],
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
        return item
    except Exception as exc:
        raise InfraError(f"MCQ generation failed: {source['source_id']}") from exc
