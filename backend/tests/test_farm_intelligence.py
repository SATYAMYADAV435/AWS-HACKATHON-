"""
Unit and integration tests for personalized farm intelligence and crop image diagnosis.
"""

from fastapi.testclient import TestClient
from backend.local_server import app
from backend.schemas import FarmerProfile
from backend.farm_intelligence import compute_farm_intelligence
from backend.image_analyzer import analyze_crop_image

client = TestClient(app)

def test_compute_farm_intelligence_basic():
    profile = FarmerProfile(
        farm_name="Mala Farm",
        district="nashik",
        acres=3.5,
        soil_type="medium_black",
        soil_ph="6.8",
        water_source="well",
        irrigation_type="drip",
        current_crop="onion",
        crop_stage="vegetative"
    )
    intel = compute_farm_intelligence(profile)
    assert intel["farm_name"] == "Mala Farm"
    assert intel["district"] == "nashik"
    assert 0 <= intel["farm_health_score"] <= 100
    assert 0 <= intel["soil_health_score"] <= 100
    assert intel["crop_health_risk"] in ("low", "moderate", "high")
    assert len(intel["personalized_recommendations"]) > 0
    assert len(intel["suggested_prompts"]) > 0
    assert "weather_summary" in intel

def test_api_regions_endpoint():
    res = client.get("/api/regions")
    assert res.status_code == 200
    data = res.json()
    assert "districts" in data
    assert "state_languages" in data
    assert any(d["id"] == "nashik" for d in data["districts"])
    assert "Maharashtra" in data["state_languages"]
    assert "Gujarat" in data["state_languages"]

def test_api_farm_intelligence_endpoint():
    payload = {
        "farm_name": "Shivar 1",
        "district": "pune",
        "acres": 4.0,
        "soil_type": "alluvial_clay",
        "soil_ph": "7.2",
        "water_source": "canal",
        "irrigation_type": "flood",
        "current_crop": "wheat",
        "crop_stage": "flowering"
    }
    res = client.post("/api/farm-intelligence", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["farm_name"] == "Shivar 1"
    assert "farm_health_score" in data

def test_api_crop_image_analysis():
    payload = {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "mime_type": "image/png",
        "farm_context": {
            "current_crop": "onion",
            "crop_stage": "vegetative",
            "district": "nashik"
        }
    }
    res = client.post("/api/crop-image-analysis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "condition" in data
    assert "risk_level" in data
    assert "recommended_actions" in data
    assert "confidence_pct" in data
    assert "disclaimer" in data

def test_chat_pipeline_with_farm_context():
    payload = {
        "text": "माझ्या शेतात काय करावे?",
        "language": "mr",
        "farm_name": "Gat No 42",
        "district": "nashik",
        "acres": 5.0,
        "soil_type": "medium_black",
        "soil_ph": "6.8",
        "water_source": "borewell",
        "irrigation_type": "drip",
        "current_crop": "onion",
        "crop_stage": "bulb_formation"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    assert "title" in card
    assert "summary_lines" in card
    assert len(card["summary_lines"]) <= 3
