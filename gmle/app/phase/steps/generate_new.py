"""Phase 4: Generate New."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.api.internal.generation_api import get_generation_api
from gmle.app.infra.logger import get_logger, with_fields
from gmle.app.sot.queue_io import read_queue


def execute(context: Dict[str, Any]) -> None:
    """Generate New items (Phase 4)."""
    logger = get_logger(space_id=context.get("space_id"))
    
    if context.get("mode") == "batch":
        context["new_source_ids"] = []
        logger.debug("Batch mode: skipping MCQ generation")
        return
    
    paths = context["paths"]
    params = context["params"]
    plan = context.get("plan", {})
    # Use plan.new_total if available, otherwise fallback to params.new_total
    new_total = plan.get("new_total", params.get("new_total", 10))
    items = context["items"]
    ledger = context["ledger"]
    used_source_ids = {r["source_id"] for r in ledger}

    sources = read_queue(paths["queue"])
    available_sources = [s for s in sources if s["source_id"] not in used_source_ids]
    
    logger.info("Starting MCQ generation", **with_fields(logger,
        new_total=new_total,
        available_sources=len(available_sources),
        run_id=context.get("run_id"),
    ))
    
    new_items: list[Dict[str, Any]] = []
    new_source_ids: list[str] = []
    generated_count = 0
    
    # Get generation API instance
    generation_api = get_generation_api(config=context)
    
    for source in available_sources:
        if len(new_items) >= new_total:
            break
        item = generation_api.generate_mcq(source, config=context)
        generated_count += 1
        if item:
            new_items.append(item)
            new_source_ids.append(source["source_id"])
            logger.debug("MCQ generated successfully", **with_fields(logger,
                source_id=source["source_id"],
                title=source.get("title", "")[:50],
            ))

    items.extend(new_items)
    context["items"] = items
    context["new_source_ids"] = new_source_ids
    context["new_generated"] = generated_count
    
    logger.info("MCQ generation completed", **with_fields(logger,
        new_total=new_total,
        generated=generated_count,
        accepted=len(new_items),
        run_id=context.get("run_id"),
    ))
