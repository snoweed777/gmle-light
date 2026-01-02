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
    
    # Check API rate limit before starting
    from gmle.app.http.usage_tracker import get_usage_tracker
    from gmle.app.config.getter import get_llm_config, get_rate_limit_config
    
    llm_config = get_llm_config(context)
    active_provider = llm_config.get("active_provider", "huggingface")
    rate_limit_config = get_rate_limit_config(context)
    
    # Get limits for mcq_generation call type
    call_type_limits = rate_limit_config.get("call_type_limits", {})
    mcq_limits = call_type_limits.get("mcq_generation", {})
    default_rph = rate_limit_config.get("requests_per_hour", 500)
    
    limits = {
        "requests_per_hour": mcq_limits.get("requests_per_hour", default_rph),
    }
    
    usage_tracker = get_usage_tracker()
    can_acquire, reason = usage_tracker.can_acquire("mcq_generation", active_provider, limits)
    
    if not can_acquire:
        logger.warning("API rate limit check failed, skipping generation", **with_fields(logger,
            provider=active_provider,
            reason=reason,
            run_id=context.get("run_id"),
        ))
        context["new_source_ids"] = []
        context["failed_source_ids"] = []
        context["new_generated"] = 0
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
    
    # Filter sources by excerpt length with params
    excerpt_max = params.get("excerpt_max", 650)
    excerpt_min = params.get("excerpt_min", 200)
    
    available_sources = [
        s for s in sources 
        if s["source_id"] not in used_source_ids
        and excerpt_min <= len(s.get("excerpt", "")) <= excerpt_max
    ]
    
    # Count filtered sources for logging
    total_unused = len([s for s in sources if s["source_id"] not in used_source_ids])
    filtered_count = total_unused - len(available_sources)
    
    logger.info("Starting MCQ generation", **with_fields(logger,
        new_total=new_total,
        available_sources=len(available_sources),
        filtered_by_length=filtered_count,
        excerpt_min=excerpt_min,
        excerpt_max=excerpt_max,
        run_id=context.get("run_id"),
    ))
    
    new_items: list[Dict[str, Any]] = []
    new_source_ids: list[str] = []
    failed_source_ids: list[str] = []
    generated_count = 0
    
    # Get generation API instance
    generation_api = get_generation_api(config=context)
    
    for source in available_sources:
        if len(new_items) >= new_total:
            break
        
        try:
            item = generation_api.generate_mcq(source, config=context)
            generated_count += 1
            if item:
                new_items.append(item)
                new_source_ids.append(source["source_id"])
                logger.debug("MCQ generated successfully", **with_fields(logger,
                    source_id=source["source_id"],
                    title=source.get("title", "")[:50],
                ))
            else:
                # None returned = hard_gate failed or no facts extracted
                failed_source_ids.append(source["source_id"])
                logger.warning("MCQ generation returned None (likely hard_gate failed)", 
                    **with_fields(logger, 
                        source_id=source["source_id"],
                        title=source.get("title", "")[:50],
                    ))
        except Exception as exc:
            # Exception occurred, skip this source and continue
            failed_source_ids.append(source["source_id"])
            logger.error("MCQ generation failed with exception, skipping source", 
                **with_fields(logger, 
                    source_id=source["source_id"],
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    title=source.get("title", "")[:50],
                ))
            continue  # Skip to next source

    items.extend(new_items)
    context["items"] = items
    context["new_source_ids"] = new_source_ids
    context["failed_source_ids"] = failed_source_ids
    context["new_generated"] = generated_count
    
    logger.info("MCQ generation completed", **with_fields(logger,
        new_total=new_total,
        generated=generated_count,
        accepted=len(new_items),
        failed=len(failed_source_ids),
        run_id=context.get("run_id"),
    ))
