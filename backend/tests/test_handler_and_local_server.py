"""
Tests for backend/handler.py and backend/local_server.py (T-04 verification).
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.handler import lambda_handler, get_hello_card
from backend.local_server import app

client = TestClient(app)

def test_lambda_handler_options_cors():
    event = {
        "requestContext": {"http": {"method": "OPTIONS"}},
        "rawPath": "/chat"
    }
    res = lambda_handler(event)
    assert res["statusCode"] == 200
    assert res["headers"]["Access-Control-Allow-Origin"] == "*"

def test_lambda_handler_health():
    event = {
        "requestContext": {"http": {"method": "GET"}},
        "rawPath": "/health"
    }
    res = lambda_handler(event)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["status"] == "ok"

@pytest.mark.parametrize("lang", ["mr", "hi", "en"])
def test_lambda_handler_chat_hello_card(lang):
    event = {
        "requestContext": {"http": {"method": "POST"}},
        "rawPath": "/chat",
        "body": json.dumps({"language": lang, "text": "hello"})
    }
    res = lambda_handler(event)
    assert res["statusCode"] == 200
    assert res["headers"]["Access-Control-Allow-Origin"] == "*"
    card = json.loads(res["body"])
    
    # Contract verification per ARCHITECTURE.md §3
    assert "title" in card
    assert "summary_lines" in card
    assert len(card["summary_lines"]) <= 3
    assert "steps" in card
    assert len(card["steps"]) <= 3
    assert "labels" in card
    assert "sources" in card
    assert "speak_text" in card
    assert card["language"] == lang

def test_fastapi_local_server_chat():
    res = client.post("/chat", json={"language": "mr", "text": "नमस्कार"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "*"
    data = res.json()
    assert data["language"] == "mr"
    assert "title" in data
    assert "speak_text" in data
