"""Common JSON parsing utilities for LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, cast


def extract_json_from_text(text: str) -> str | None:
    """Extract JSON string from text that may contain markdown code blocks or other formatting.
    
    Args:
        text: Text that may contain JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    if not isinstance(text, str):
        return None
    
    # Try to find JSON in markdown code blocks first
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find first complete JSON object (with proper brace matching)
    # This handles cases where there might be multiple JSON objects or trailing text
    brace_count = 0
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                # Found complete JSON object
                return text[start_idx:i+1]
    
    # Fallback: try original regex approach
    json_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    return None


def parse_llm_response(response: Any) -> Dict[str, Any]:
    """Parse LLM response and extract JSON if present.
    
    Handles various response formats:
    - Direct JSON dict
    - Text containing JSON
    - Text containing markdown code blocks with JSON
    
    Args:
        response: LLM API response (dict or str)
        
    Returns:
        Parsed JSON dict, or dict with "text" key containing original response
    """
    from gmle.app.infra.logger import get_logger, with_fields
    logger = get_logger()
    
    # If already a dict, check if it contains text to parse
    if isinstance(response, dict):
        # Check for common response formats
        if "text" in response:
            text = response["text"]
            json_str = extract_json_from_text(text)
            if json_str:
                try:
                    return cast(Dict[str, Any], json.loads(json_str))
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("JSON parse failed from text field", **with_fields(logger,
                        error=str(exc),
                        json_str_preview=json_str[:300],
                        json_str_length=len(json_str),
                    ))
                    pass
            return response
        
        # Check for OpenAI-compatible format
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                json_str = extract_json_from_text(content)
                if json_str:
                    try:
                        return cast(Dict[str, Any], json.loads(json_str))
                    except (json.JSONDecodeError, ValueError) as exc:
                        logger.warning("JSON parse failed from OpenAI format", **with_fields(logger,
                            error=str(exc),
                            json_str_preview=json_str[:300],
                        ))
                        pass
                # Return in a format compatible with our system
                return {
                    "content": content,
                    "model": response.get("model", ""),
                    "usage": response.get("usage", {}),
                }
        
        # Check for Gemini format
        if "candidates" in response and len(response["candidates"]) > 0:
            candidate = response["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if len(parts) > 0 and "text" in parts[0]:
                    text = parts[0]["text"]
                    json_str = extract_json_from_text(text)
                    if json_str:
                        try:
                            return cast(Dict[str, Any], json.loads(json_str))
                        except (json.JSONDecodeError, ValueError) as exc:
                            logger.warning("JSON parse failed from Gemini format", **with_fields(logger,
                                error=str(exc),
                                json_str_preview=json_str[:300],
                            ))
                            pass
                    return {"text": text}
        
        # Already a dict, return as-is
        return response
    
    # If string, try to parse as JSON
    if isinstance(response, str):
        json_str = extract_json_from_text(response)
        if json_str:
            try:
                return cast(Dict[str, Any], json.loads(json_str))
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("JSON parse failed from string response", **with_fields(logger,
                    error=str(exc),
                    json_str_preview=json_str[:300],
                    response_preview=response[:200],
                ))
                pass
        return {"text": response}
    
    # Fallback: wrap in dict
    return {"text": str(response)}

