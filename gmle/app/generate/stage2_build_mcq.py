"""Stage-2 Build MCQ (spec 15.2)."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.http.llm_client import chat_completions


def build_mcq(facts: List[Dict[str, Any]], relations: List[Dict[str, Any]], excerpt: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build MCQ from facts/relations (spec 15.2)."""
    facts_text = "\n".join([f"- {f['id']}: {f['text']}" for f in facts])
    relations_text = "\n".join([f"- {r['id']}: {r['text']}" for r in relations])
    prompt = f"""Create a 4-choice MCQ using only these facts and relations.
Distractors must use vocabulary from the excerpt.
Rationale quote must be ≤100 chars and a substring of the excerpt.

Facts:
{facts_text}

Relations:
{relations_text}

Excerpt:
{excerpt}

Return JSON:
{{
  "question": "...",
  "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "answer": "A|B|C|D",
  "rationale": {{"quote": "...", "explain": "..."}},
  "format": "F|W|A",
  "depth": 1|2|3
}}"""
    response = chat_completions({
        "messages": [{"role": "user", "content": prompt}],
    }, config=config)
    if isinstance(response, dict):
        return response
    return {}
