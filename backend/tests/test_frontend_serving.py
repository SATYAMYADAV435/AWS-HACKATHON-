"""
Tests for serving frontend static assets and mock data via local_server.py.
"""

from fastapi.testclient import TestClient
from backend.local_server import app

client = TestClient(app)

def test_index_html_serving():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    content = res.text
    assert "KisanMitra" in content or "किसान मित्र" in content
    assert "hero-mic-btn" in content
    assert "chips-container" in content
    assert "result-bottom-sheet" in content

def test_i18n_files_serving():
    for lang in ["mr", "hi", "en"]:
        res = client.get(f"/i18n/{lang}.json")
        assert res.status_code == 200
        data = res.json()
        assert "app_title" in data
        assert "welcome_greeting" in data
        assert "feature_grid" in data
        assert "prompts" in data
        assert len(data["prompts"]) >= 3

def test_mock_files_serving():
    mock_flows = ["what_to_grow", "weather_today", "prices", "how_to_grow"]
    for flow in mock_flows:
        res = client.get(f"/mock/{flow}_mr.json")
        assert res.status_code == 200
        data = res.json()
        assert "title" in data
        assert "summary_lines" in data
        assert "speak_text" in data
        assert data["language"] == "mr"

def test_javascript_files_serving():
    res_speech = client.get("/speech.js")
    assert res_speech.status_code == 200
    assert "KisanSpeech" in res_speech.text

    res_app = client.get("/app.js")
    assert res_app.status_code == 200
    assert "KisanApp" in res_app.text
