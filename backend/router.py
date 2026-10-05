"""
KisanMitra — backend/router.py
Classifier and router module invoking Bedrock with router.md system prompt per ARCHITECTURE.md §1 & §2.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from backend.bedrock_client import invoke_model
from backend.schemas import RouterOutput

logger = logging.getLogger("kisanmitra.router")

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
ROUTER_PROMPT_FILE = PROMPTS_DIR / "router.md"

_router_system_prompt: Optional[str] = None

def _get_router_system_prompt() -> str:
    global _router_system_prompt
    if _router_system_prompt is not None:
        return _router_system_prompt
    if ROUTER_PROMPT_FILE.exists():
        with open(ROUTER_PROMPT_FILE, "r", encoding="utf-8") as f:
            _router_system_prompt = f.read()
    else:
        _router_system_prompt = "You are the KisanMitra router. Output JSON with intent, crop, and language."
    return _router_system_prompt

def _clean_json_response(raw_text: str) -> str:
    """Strips markdown code blocks and whitespace."""
    text = re.sub(r"^```(?:json)?", "", raw_text.strip(), flags=re.MULTILINE)
    text = re.sub(r"```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()

def route_query(
    text: str,
    default_lang: str = "mr",
    explicit_intent: Optional[str] = None,
    explicit_crop: Optional[str] = None
) -> RouterOutput:
    """
    Classifies raw question text into {intent, crop, language}.
    Supports mixed-language input (Hinglish, Marathish, Devanagari).
    If explicit_intent is provided (e.g. 1-tap card click), routes directly.
    """
    # 1. Handle 1-tap direct feature card clicks
    if explicit_intent and explicit_intent in ("what_to_grow", "weather_today", "prices", "how_to_grow", "unknown"):
        return RouterOutput(
            intent=explicit_intent,
            crop=explicit_crop,
            language=default_lang
        )

    clean_text = (text or "").strip()
    if not clean_text:
        return RouterOutput(
            intent="what_to_grow",
            crop=None,
            language=default_lang
        )

    system_prompt = _get_router_system_prompt()
    user_prompt = f"User Question: \"{clean_text}\"\nUser Default Language Preference: \"{default_lang}\""

    try:
        raw_response = invoke_model(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.1
        )
        cleaned_json = _clean_json_response(raw_response)
        data = json.loads(cleaned_json)
        return RouterOutput(
            intent=data.get("intent", "what_to_grow"),
            crop=data.get("crop"),
            language=data.get("language", default_lang)
        )
    except Exception as exc:
        logger.warning(f"Router parsing error ({exc}), using safe fallback.")
        # Safe fallback
        return RouterOutput(
            intent="what_to_grow",
            crop=None,
            language=default_lang
        )
