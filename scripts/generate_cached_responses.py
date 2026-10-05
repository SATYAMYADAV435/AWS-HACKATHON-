"""
KisanMitra — scripts/generate_cached_responses.py
Generates and verifies saved responses for 3 demo personas x 4 flows (T-22).
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
CACHE_DIR = BASE_DIR / "fallback" / "cached_responses"

FLOWS = ["what_to_grow", "weather_today", "prices", "how_to_grow"]

def generate_all():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    total = 0
    for p in profiles:
        persona_id = p["id"]
        lang = p["language"]
        district = p["district"]
        acres = p["acres"]
        water = p["water_source"]

        for flow in FLOWS:
            payload = {
                "intent": flow,
                "language": lang,
                "district": district,
                "acres": acres,
                "water_source": water,
                "crop": "onion" if flow in ("prices", "how_to_grow") else None
            }
            res = process_chat_request(payload)
            # Validate schema
            card = AnswerCard(**res)

            out_file = CACHE_DIR / f"{persona_id}_{flow}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(card.model_dump(), f, ensure_ascii=False, indent=2)

            print(f"Generated: {out_file.name} ({card.language}) -> {card.title}")
            total += 1

    print(f"\nSuccessfully generated {total} cached responses in fallback/cached_responses/.")

if __name__ == "__main__":
    generate_all()
