"""
KisanMitra — scripts/persona_runthrough.py
Full voice run-through of all 3 demo personas end-to-end, twice (T-27).
Verifies Sunita, Rajesh, and John across all four core agricultural scenarios.
"""

import os
import sys
import json
from pathlib import Path

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.handler import process_chat_request
from backend.schemas import AnswerCard

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILES_FILE = BASE_DIR / "data" / "demo_profiles.json"

QUERIES_BY_LANG = {
    "mr": [
        ("आता रब्बी हंगामात कोणते पीक घ्यावे?", "what_to_grow"),
        ("आज शेतात फवारणी करू का?", "weather_today"),
        ("नाशिक बाजारात कांद्याला काय भाव आहे?", "prices"),
        ("रब्बी कांदा लागवड कशी करावी?", "how_to_grow")
    ],
    "hi": [
        ("अभी रबी के मौसम में कौन सी फसल लगाएं?", "what_to_grow"),
        ("क्या आज खेत में छिड़काव कर सकते हैं?", "weather_today"),
        ("नासिक मंडी में प्याज का क्या भाव है?", "prices"),
        ("रबी प्याज की खेती कैसे करें?", "how_to_grow")
    ],
    "en": [
        ("Which crop should I grow in rabi season?", "what_to_grow"),
        ("Can I spray pesticide today?", "weather_today"),
        ("What is the current onion price in mandi?", "prices"),
        ("How to cultivate rabi onion?", "how_to_grow")
    ]
}

def run_rehearsal(iteration: int):
    print(f"\n==========================================")
    print(f"   DEMO PERSONA REHEARSAL — PASS {iteration}")
    print(f"==========================================")

    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    for p in profiles:
        p_name = p["name"]
        p_lang = p["language"]
        p_dist = p["district"]
        p_acres = p["acres"]
        p_water = p["water_source"]

        print(f"\n>>> Persona: {p_name} ({p_dist.upper()}, {p_lang.upper()}, {p_acres} ac, {p_water})")

        queries = QUERIES_BY_LANG[p_lang]
        for idx, (q_text, expected_flow) in enumerate(queries, 1):
            payload = {
                "text": q_text,
                "language": p_lang,
                "district": p_dist,
                "acres": p_acres,
                "water_source": p_water
            }
            res = process_chat_request(payload)
            card = AnswerCard(**res)

            # Contract checks
            assert card.language == p_lang
            assert len(card.title) > 0
            assert len(card.summary_lines) <= 3
            assert len(card.steps) <= 3
            assert len(card.speak_text) > 0
            assert len(card.metrics) > 0

            print(f"  Step {idx} [{expected_flow}]: '{q_text}'")
            print(f"    -> Card: {card.title}")
            print(f"    -> Speak: {card.speak_text[:65]}...")
            metric_strs = [f"{m.label}: {m.value}" for m in card.metrics]
            print(f"    -> Metrics: {' | '.join(metric_strs)}")

    print(f"\nPass {iteration} completed successfully for all 3 personas!")

if __name__ == "__main__":
    run_rehearsal(iteration=1)
    run_rehearsal(iteration=2)
    print("\n✅ All 3 demo personas completed two end-to-end rehearsals successfully!")
