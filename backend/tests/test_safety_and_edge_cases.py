"""
KisanMitra — backend/tests/test_safety_and_edge_cases.py
Edge-case safety tests for T-21 and RULES.md §1:
1. No-source -> KVK sentence
2. Router 'unknown' -> friendly capabilities reply
3. Strict schema limits (<=3 summary lines, <=3 steps)
4. No mixed scripts in speak_text
"""

import pytest
from backend.handler import process_chat_request
from backend.agents.crop_guide import run_crop_guide_agent
from backend.schemas import FarmerProfile, AnswerCard

def test_crop_guide_no_source_safety():
    """Verify missing crop guide outputs mandatory KVK/Kisan Call Centre fallback sentence."""
    profile = FarmerProfile(district="nashik", acres=2.0, water_source="well", language="mr")
    result = run_crop_guide_agent(profile, crop="unknown_dragonfruit_crop")

    assert result.agent == "crop_guide"
    assert "कृषी विज्ञान केंद्राशी (KVK)" in result.finding
    assert "1800-180-1551" in result.finding

@pytest.mark.parametrize("lang, expected_title", [
    ("mr", "किसान मित्र सहाय्य"),
    ("hi", "किसान मित्र सहायता"),
    ("en", "KisanMitra Capabilities")
])
def test_router_unknown_intent_capabilities(lang, expected_title):
    """Verify off-topic queries return friendly capabilities card in user's language."""
    payload = {
        "text": "How can I get a loan to buy a second-hand tractor from SBI?",
        "language": lang,
        "district": "nashik"
    }
    res = process_chat_request(payload)

    assert res["language"] == lang
    assert res["title"] == expected_title
    assert len(res["summary_lines"]) <= 3
    assert len(res["steps"]) <= 3
    assert "speak_text" in res
    assert len(res["speak_text"]) > 0

    # Validate schema
    card = AnswerCard(**res)
    assert card.language == lang

def test_safety_never_dead_end_empty_payload():
    """Verify empty or corrupted payload never crashes and returns safe card."""
    res = process_chat_request({})
    assert "title" in res
    assert "speak_text" in res
    assert res["language"] == "mr"
    card = AnswerCard(**res)
    assert card is not None

def test_no_english_script_in_devanagari_speak_text():
    """Verify Marathi and Hindi speak_text contain zero mixed English/Latin characters."""
    for q_mr in ["कांद्याचा आजचा भाव काय आहे?", "आज फवारणी करावी का?"]:
        res_mr = process_chat_request({"text": q_mr, "language": "mr", "district": "nashik"})
        speak = res_mr["speak_text"]
        # Allow numbers and punctuation, but zero Latin alpha characters
        latin_chars = [c for c in speak if c.isascii() and c.isalpha()]
        assert len(latin_chars) == 0, f"Found Latin characters {latin_chars} in Marathi speak_text: {speak}"

    for q_hi in ["नासिक में प्याज का क्या रेट है?", "क्या आज दवा छिड़क सकते हैं?"]:
        res_hi = process_chat_request({"text": q_hi, "language": "hi", "district": "nashik"})
        speak = res_hi["speak_text"]
        latin_chars = [c for c in speak if c.isascii() and c.isalpha()]
        assert len(latin_chars) == 0, f"Found Latin characters {latin_chars} in Hindi speak_text: {speak}"
