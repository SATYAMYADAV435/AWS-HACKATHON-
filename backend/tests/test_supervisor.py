"""
Unit tests for backend/supervisor.py verifying AnswerCard generation and constraints.
"""

from backend.schemas import FarmerProfile, RouterOutput, AgentResult, AnswerCard
from backend.supervisor import synthesize_answer

def test_supervisor_synthesize_answer_what_to_grow():
    profile = FarmerProfile(district="nashik", acres=3.0, water_source="well", language="mr")
    router_out = RouterOutput(intent="what_to_grow", crop=None, language="mr")

    findings = [
        AgentResult(
            agent="weather",
            finding="Weather is sunny and dry; no rain expected.",
            risk="low",
            evidence=["Temp: 29C"],
            data_source="cache"
        ),
        AgentResult(
            agent="market",
            finding="Onion modal price is 1850 Rs per quintal with positive trend.",
            risk="low",
            evidence=["Price: 1850"],
            data_source="csv"
        )
    ]

    recommender_data = {
        "recommended_crops": [
            {
                "crop_id": "onion",
                "gross_income_per_acre": 140000,
                "duration_days": {"min": 110, "max": 125},
                "price_trend": {"pct_change": 8.0, "direction": "up"}
            }
        ]
    }

    card = synthesize_answer(router_out, profile, findings, recommender_data)

    assert isinstance(card, AnswerCard)
    assert len(card.summary_lines) <= 3
    assert len(card.steps) <= 3
    assert len(card.labels) >= 1
    assert len(card.sources) >= 1
    assert card.language == "mr"
    assert card.metrics is not None
    assert len(card.metrics) <= 3
    assert card.speak_text != ""
