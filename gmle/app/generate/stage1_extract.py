"""Stage-1 Extract (spec 15.1)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.http.llm_client import chat_completions


def extract_facts_relations(excerpt: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Extract facts and relations from excerpt (spec 15.1)."""
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
        "messages": [{"role": "user", "content": prompt}],
    }, config=config)
    if isinstance(response, dict):
        return response
    return {}
