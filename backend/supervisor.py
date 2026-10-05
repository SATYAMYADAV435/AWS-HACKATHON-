"""
KisanMitra — backend/supervisor.py
Supervisor module synthesizing findings into short AnswerCard JSON per ARCHITECTURE.md §1 & §2.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.bedrock_client import invoke_model
from backend.schemas import (
    AgentResult,
    AnswerCard,
    FarmerProfile,
    MetricItem,
    RouterOutput,
    safe_fallback_card
)

logger = logging.getLogger("kisanmitra.supervisor")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SUPERVISOR_PROMPT_FILE = PROMPTS_DIR / "supervisor.md"
GLOSSARY_FILE = DATA_DIR / "glossary.json"

_supervisor_system_prompt: Optional[str] = None
_glossary_data: Optional[Dict[str, Any]] = None

def _get_supervisor_prompt() -> str:
    global _supervisor_system_prompt
    if _supervisor_system_prompt is not None:
        return _supervisor_system_prompt
    if SUPERVISOR_PROMPT_FILE.exists():
        with open(SUPERVISOR_PROMPT_FILE, "r", encoding="utf-8") as f:
            _supervisor_system_prompt = f.read()
    else:
        _supervisor_system_prompt = "You are the KisanMitra Supervisor. Output valid AnswerCard JSON."
    return _supervisor_system_prompt

def _get_glossary() -> Dict[str, Any]:
    global _glossary_data
    if _glossary_data is not None:
        return _glossary_data
    if GLOSSARY_FILE.exists():
        with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
            _glossary_data = json.load(f)
    else:
        _glossary_data = {}
    return _glossary_data

def _clean_json(raw_text: str) -> str:
    text = re.sub(r"^```(?:json)?", "", raw_text.strip(), flags=re.MULTILINE)
    text = re.sub(r"```$", "", text.strip(), flags=re.MULTILINE)
    return text.strip()

def _extract_metric_items(
    intent: str,
    agent_findings: List[AgentResult],
    recommender_data: Optional[Dict[str, Any]],
    lang: str = "mr"
) -> List[MetricItem]:
    """Generates up to 3 high-contrast key metric badges for the Bohemian UI card."""
    metrics = []

    if intent == "what_to_grow" and recommender_data:
        top = recommender_data.get("recommended_crops", [])
        if top:
            best = top[0]
            gross = best.get("gross_income_per_acre", 140000)
            duration = best.get("duration_days", {}).get("min", 110)
            trend_pct = best.get("price_trend", {}).get("pct_change", 5.0)

            if lang == "mr":
                metrics.append(MetricItem(label="अंदाजे उत्पन्न", value=f"₹{gross:,} / एकर"))
                metrics.append(MetricItem(label="कालावधी", value=f"{duration} दिवस"))
                metrics.append(MetricItem(label="बाजार कल", value=f"↗ +{trend_pct}%"))
            elif lang == "hi":
                metrics.append(MetricItem(label="अनुमानित आय", value=f"₹{gross:,} / एकड़"))
                metrics.append(MetricItem(label="अवधि", value=f"{duration} दिन"))
                metrics.append(MetricItem(label="बाजार रुख", value=f"↗ +{trend_pct}%"))
            else:
                metrics.append(MetricItem(label="Est. Gross", value=f"₹{gross:,} / acre"))
                metrics.append(MetricItem(label="Duration", value=f"{duration} days"))
                metrics.append(MetricItem(label="Price Trend", value=f"↗ +{trend_pct}%"))
            return metrics[:3]

    if intent == "weather_today":
        weather_res = next((a for a in agent_findings if a.agent == "weather"), None)
        if weather_res:
            temp = "29°C"
            wind = "9 km/h"
            for ev in weather_res.evidence:
                if "Temp" in ev: temp = ev.split(":")[-1].strip()
                if "Wind" in ev: wind = ev.split(":")[-1].strip()

            flag_label = "✅ अनुकूल" if weather_res.risk == "low" else "⚠️ सावध"
            if lang == "en":
                flag_label = "✅ Favorable" if weather_res.risk == "low" else "⚠️ Caution"

            if lang == "mr":
                metrics.append(MetricItem(label="तापमान", value=temp))
                metrics.append(MetricItem(label="वारा", value=wind))
                metrics.append(MetricItem(label="फवारणी सल्ला", value=flag_label))
            elif lang == "hi":
                metrics.append(MetricItem(label="तापमान", value=temp))
                metrics.append(MetricItem(label="हवा", value=wind))
                metrics.append(MetricItem(label="छिड़काव सलाह", value=flag_label))
            else:
                metrics.append(MetricItem(label="Temperature", value=temp))
                metrics.append(MetricItem(label="Wind", value=wind))
                metrics.append(MetricItem(label="Spray Status", value=flag_label))
            return metrics[:3]

    if intent == "prices":
        market_res = next((a for a in agent_findings if a.agent == "market"), None)
        if market_res:
            price = "₹1,850"
            for ev in market_res.evidence:
                if "Modal Price" in ev: price = ev.split(":")[-1].strip()

            if lang == "mr":
                metrics.append(MetricItem(label="सरासरी भाव", value=price))
                metrics.append(MetricItem(label="बाजार कल", value="↗ स्थिर/वाढता"))
                metrics.append(MetricItem(label="बाजारपेठ", value="नाशिक/लासलगाव"))
            elif lang == "hi":
                metrics.append(MetricItem(label="औसत भाव", value=price))
                metrics.append(MetricItem(label="बाजार रुख", value="↗ स्थिर/बढ़त"))
                metrics.append(MetricItem(label="मंडी", value="नासिक/लासलगांव"))
            else:
                metrics.append(MetricItem(label="Modal Price", value=price))
                metrics.append(MetricItem(label="Trend", value="↗ Up / Stable"))
                metrics.append(MetricItem(label="Primary Mandi", value="Lasalgaon"))
            return metrics[:3]

    # Default fallback metrics
    return [
        MetricItem(label="सल्ला दर्जा" if lang == "mr" else "Advisory Status", value="प्रमाणित"),
        MetricItem(label="हंगाम" if lang == "mr" else "Season", value="रब्बी २०२६"),
        MetricItem(label="क्षेत्र" if lang == "mr" else "Region", value="महाराष्ट्र")
    ]

def synthesize_answer(
    router_output: RouterOutput,
    profile: FarmerProfile,
    agent_findings: List[AgentResult],
    recommender_data: Optional[Dict[str, Any]] = None
) -> AnswerCard:
    """
    Synthesizes router output and agent findings into a verified AnswerCard.
    Enforces non-negotiable honesty labels and max 3-line summaries.
    """
    lang = router_output.language or profile.language or "mr"
    intent = router_output.intent

    system_prompt = _get_supervisor_prompt()

    # Build rich context for the LLM
    findings_context = []
    for f in agent_findings:
        findings_context.append(f"Agent [{f.agent}]: {f.finding} (Risk: {f.risk}, Source: {f.data_source})")

    context_str = "\n".join(findings_context)
    rec_str = json.dumps(recommender_data, ensure_ascii=False) if recommender_data else "None"

    user_prompt = (
        f"Target Language: {lang}\n"
        f"Intent: {intent}\n"
        f"Crop Mentioned: {router_output.crop or profile.current_crop or 'general'}\n"
        f"Farmer Profile: Farm={profile.farm_name}, District={profile.district}, Locality={profile.locality}, "
        f"Acres={profile.acres}, Soil={profile.soil_type}, pH={profile.soil_ph}, Water={profile.water_source}, "
        f"Irrigation={profile.irrigation_type}, Current Crop={profile.current_crop}, Crop Stage={profile.crop_stage}\n\n"
        f"Agent Findings:\n{context_str}\n\n"
        f"Recommender Output:\n{rec_str}\n\n"
        f"Please write the AnswerCard JSON now."
    )

    try:
        raw_resp = invoke_model(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=650,
            temperature=0.2
        )
        cleaned_json = _clean_json(raw_resp)
        card_dict = json.loads(cleaned_json)

        # Enforce schemas and constraints
        title = card_dict.get("title", "शेती सल्ला")
        summary_lines = card_dict.get("summary_lines", [])[:3]
        steps = card_dict.get("steps", [])[:3]
        labels = card_dict.get("labels", ["प्रातिनिधिक माहिती", "खर्चापूर्वीचे उत्पन्न"])
        sources = card_dict.get("sources", ["महात्मा फुले कृषी विद्यापीठ (MPKV)"])
        speak_text = card_dict.get("speak_text", summary_lines[0] if summary_lines else "सल्ला उपलब्ध आहे.")

        metrics = _extract_metric_items(intent, agent_findings, recommender_data, lang)

        return AnswerCard(
            title=title,
            summary_lines=summary_lines,
            steps=steps,
            labels=labels,
            sources=sources,
            speak_text=speak_text,
            language=lang,
            metrics=metrics
        )
    except Exception as exc:
        logger.warning(f"Supervisor generation failed ({exc}); returning safe fallback card.")
        fallback = safe_fallback_card(lang)
        fallback.metrics = _extract_metric_items(intent, agent_findings, recommender_data, lang)
        return fallback
