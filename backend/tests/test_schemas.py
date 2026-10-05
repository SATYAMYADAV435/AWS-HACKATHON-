"""
Tests for backend/schemas.py validating contracts and safe fallback handling.
"""

from backend.schemas import (
    FarmerProfile,
    RouterOutput,
    AgentResult,
    AnswerCard,
    safe_fallback_card,
    validate_answer_card_dict
)

def test_farmer_profile_defaults_and_normalization():
    p = FarmerProfile()
    assert p.district == "nashik"
    assert p.acres == 3.0
    assert p.language == "mr"

    p2 = FarmerProfile(district=" Pune ", language="HI")
    assert p2.district == "pune"
    assert p2.language == "hi"

def test_router_output_validation():
    r = RouterOutput(intent="what_to_grow", crop="Onion", language="MR")
    assert r.intent == "what_to_grow"
    assert r.crop == "onion"
    assert r.language == "mr"

    r_invalid = RouterOutput(intent="buy_tractor", crop="None")
    assert r_invalid.intent == "unknown"
    assert r_invalid.crop is None

def test_agent_result_contract():
    res = AgentResult(
        agent="weather",
        finding="No rain predicted next 48 hours; calm wind conditions.",
        risk="low",
        evidence=["temperature: 30C", "humidity: 45%"],
        data_source="open-meteo"
    )
    assert res.agent == "weather"
    assert res.risk == "low"
    assert len(res.evidence) == 2

def test_answer_card_caps_three_items():
    card = AnswerCard(
        title="Test Card",
        summary_lines=["line 1", "line 2", "line 3", "extra line 4"],
        steps=["step 1", "step 2", "step 3", "extra step 4"],
        speak_text="This is spoken text.",
        language="mr"
    )
    assert len(card.summary_lines) == 3
    assert len(card.steps) == 3

def test_validate_answer_card_dict_safe_fallback():
    # Invalid card missing required fields
    broken_data = {"title": "incomplete"}
    fallback = validate_answer_card_dict(broken_data, lang="mr")
    assert "title" in fallback
    assert len(fallback["summary_lines"]) <= 3
    assert "speak_text" in fallback
    assert fallback["language"] == "mr"
