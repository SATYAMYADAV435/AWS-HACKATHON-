"""
End-to-end integration tests for POST /chat pipeline (T-16 verification).
Verifies: router -> parallel agents -> recommender/guide -> supervisor -> validated AnswerCard.
"""

from fastapi.testclient import TestClient
from backend.local_server import app

client = TestClient(app)

def test_chat_pipeline_what_to_grow_marathi():
    payload = {
        "text": "आता कोणते पीक घ्यावे?",
        "language": "mr",
        "district": "nashik",
        "acres": 3.0,
        "water_source": "well"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    assert card["language"] == "mr"
    assert "title" in card
    assert len(card["summary_lines"]) <= 3
    assert len(card["steps"]) <= 3
    assert len(card["labels"]) >= 1
    assert "speak_text" in card

def test_chat_pipeline_weather_today():
    payload = {
        "text": "आज औषध फवारणी करावी का?",
        "language": "mr",
        "district": "nashik"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    assert card["language"] == "mr"
    assert "title" in card
    assert "speak_text" in card

def test_chat_pipeline_prices_hindi():
    payload = {
        "text": "आज प्याज का मंडी भाव क्या है?",
        "language": "hi",
        "district": "nashik"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    assert card["language"] == "hi"
    assert "title" in card
    assert len(card["summary_lines"]) <= 3

def test_chat_pipeline_how_to_grow():
    payload = {
        "intent": "how_to_grow",
        "crop": "onion",
        "language": "mr",
        "district": "nashik"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    assert card["language"] == "mr"
    assert "title" in card

def test_chat_pipeline_unknown_intent():
    payload = {
        "text": "क्रिकेट मॅच कधी आहे?",
        "language": "mr"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    card = res.json()
    # Capabilities reply returned
    assert "मदत" in card["title"] or "सहाय्य" in card["title"] or "सल्ला" in card["title"]
