"""Stage-2 Build MCQ (spec 15.2)."""

from __future__ import annotations

from typing import Any, Dict, List

from gmle.app.http.llm_client import chat_completions


def build_mcq(facts: List[Dict[str, Any]], relations: List[Dict[str, Any]], excerpt: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build MCQ from facts/relations (spec 15.2)."""
    from gmle.app.infra.logger import get_logger, with_fields
    logger = get_logger()
    
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
            {"role": "system", "content": "You are a multiple-choice question (MCQ) creation assistant. All questions, choices, and explanations MUST be in Japanese. Do NOT use English or any other language.\n\nCRITICAL RULES:\n1. Return ONLY valid JSON, no markdown blocks, no extra text\n2. ALL fields are REQUIRED: question, choices (array of 4), answer (A/B/C/D), rationale (object with 'text' and 'quote')\n3. Format: {\"question\": \"...\", \"choices\": [\"A: ...\", \"B: ...\", \"C: ...\", \"D: ...\"], \"answer\": \"A\", \"rationale\": {\"text\": \"...\", \"quote\": \"...\"}}\n4. The rationale.quote MUST be ≤100 chars and found in the original text\n5. All content in Japanese"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
    }, config=config)
    
    if isinstance(response, dict):
        # Log successful parse
        has_question = "question" in response
        has_choices = "choices" in response
        has_answer = "answer" in response
        has_rationale = "rationale" in response
        logger.debug("Stage 2 response parsed", **with_fields(logger,
            response_keys=list(response.keys()),
            has_required_fields=all([has_question, has_choices, has_answer, has_rationale]),
            question_preview=response.get("question", "")[:50] if has_question else "",
        ))
        return response
    else:
        # Log failed parse with raw response preview
        logger.warning("Stage 2 returned non-dict response", **with_fields(logger,
            response_type=type(response).__name__,
            response_preview=str(response)[:300],
        ))
        return {}
