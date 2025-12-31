"""Stage-2 Build MCQ (spec 15.2)."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.http.llm_client import chat_completions


def build_mcq(facts: List[Dict[str, Any]], relations: List[Dict[str, Any]], excerpt: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build MCQ from facts/relations (spec 15.2)."""
    # Get prompt template from config
    from gmle.app.config.getter import get_prompts_config
    prompts = get_prompts_config(config)
    template = prompts.get("stage2_build_mcq", {}).get("template", "")
    
    facts_text = "\n".join([f"- {f['id']}: {f['text']}" for f in facts])
    relations_text = "\n".join([f"- {r['id']}: {r['text']}" for r in relations]) if relations else ""
    
    if template:
        # Use template from config
        prompt = template.format(facts=facts_text, relations=relations_text, excerpt=excerpt)
    else:
        # Fallback to hardcoded prompt
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
        "messages": [
            {"role": "system", "content": "あなたは日本語で多肢選択問題を作成するアシスタントです。問題文、選択肢、解説は必ず日本語で記述してください。英語や他の言語は使用しないでください。"},
            {"role": "user", "content": prompt}
        ],
    }, config=config)
    if isinstance(response, dict):
        return response
    return {}
