"""Stage-1 Extract (spec 15.1)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.http.llm_client import chat_completions


def extract_facts_relations(excerpt: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Extract facts and relations from excerpt (spec 15.1)."""
    from gmle.app.infra.logger import get_logger, with_fields
    logger = get_logger()
    
    # Get prompt template from config
    from gmle.app.config.getter import get_prompts_config
    prompts = get_prompts_config(config)
    template = prompts.get("stage1_extract", {}).get("template", "")
    
    if template:
        # Use template from config
        prompt = template.format(excerpt=excerpt)
    else:
        # Fallback to hardcoded prompt
        prompt = f"""Extract facts and relations from the following excerpt.
Each fact/relation must have a support_quote that is a substring of the excerpt.

Excerpt:
{excerpt}

Return JSON:
{{
  "facts": [{{"id": "f1", "text": "...", "support_quote": "..."}}],
  "relations": [{{"id": "r1", "text": "...", "support_quote": "..."}}]
}}"""
    
    response = chat_completions({
        "messages": [
            {"role": "system", "content": "You are a fact extraction assistant. Return all output in Japanese.\n\nCRITICAL RULES:\n1. Return ONLY valid JSON, no markdown blocks, no extra text\n2. Every fact MUST have: id, text (in Japanese), support_quote\n3. The support_quote MUST be an exact substring from the input text\n4. Format: {\"facts\": [{\"id\": \"f1\", \"text\": \"...\", \"support_quote\": \"...\"}]}"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
    }, config=config)
    
    if isinstance(response, dict):
        # Log successful parse
        facts_count = len(response.get("facts", []))
        relations_count = len(response.get("relations", []))
        logger.debug("Stage 1 response parsed", **with_fields(logger,
            facts_count=facts_count,
            relations_count=relations_count,
            response_keys=list(response.keys()),
        ))
        return response
    else:
        # Log failed parse with raw response preview
        logger.warning("Stage 1 returned non-dict response", **with_fields(logger,
            response_type=type(response).__name__,
            response_preview=str(response)[:300],
        ))
        return {}
