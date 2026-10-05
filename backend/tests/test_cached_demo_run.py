"""
KisanMitra — backend/tests/test_cached_demo_run.py
Verifies full offline demo runs with USE_CACHE=true across all 3 personas and 4 flows (T-22).
"""

import json
from pathlib import Path
import pytest
from backend.handler import process_chat_request
from backend.schemas import AnswerCard

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROFILES_FILE = BASE_DIR / "data" / "demo_profiles.json"
CACHE_DIR = BASE_DIR / "fallback" / "cached_responses"

FLOWS = ["what_to_grow", "weather_today", "prices", "how_to_grow"]

@pytest.fixture(scope="module")
def demo_profiles():
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def test_full_cached_demo_personas_and_flows(demo_profiles, monkeypatch):
    """Verify all 3 personas run through all 4 flows producing valid AnswerCards."""
    monkeypatch.setenv("USE_CACHE", "true")
    for p in demo_profiles:
        persona_id = p["id"]
        lang = p["language"]
        district = p["district"]

        for flow in FLOWS:
            payload = {
                "intent": flow,
                "language": lang,
                "district": district,
                "crop": "onion" if flow in ("prices", "how_to_grow") else None
            }
            res = process_chat_request(payload)
            card = AnswerCard(**res)

            assert card.language == lang
            assert len(card.title) > 0
            assert len(card.summary_lines) <= 3
            assert len(card.steps) <= 3
            assert len(card.speak_text) > 0
            assert len(card.metrics) > 0

            # Verify saved fallback file exists
            saved_file = CACHE_DIR / f"{persona_id}_{flow}.json"
            assert saved_file.exists()
            with open(saved_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            saved_card = AnswerCard(**saved_data)
            assert saved_card.language == lang
