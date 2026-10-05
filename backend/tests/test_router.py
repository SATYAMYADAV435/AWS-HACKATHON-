"""
Unit tests for backend/router.py verifying intent, crop, and language routing.
"""

from backend.router import route_query

def test_router_explicit_intent():
    res = route_query("", default_lang="mr", explicit_intent="weather_today")
    assert res.intent == "weather_today"
    assert res.language == "mr"

def test_router_marathi_crop_query():
    res = route_query("आता कोणते पीक घ्यावे?", default_lang="mr")
    assert res.intent == "what_to_grow"
    assert res.language == "mr"

def test_router_price_onion():
    res = route_query("कांद्याचा आजचा बाजारभाव काय आहे?", default_lang="mr")
    assert res.intent == "prices"
    assert res.crop == "onion"
    assert res.language == "mr"

def test_router_weather_spray():
    res = route_query("आज शेतात फवारणी करावी का?", default_lang="mr")
    assert res.intent == "weather_today"

def test_router_hindi_query():
    res = route_query("आज प्याज का क्या भाव है?", default_lang="hi")
    assert res.intent == "prices"
    assert res.crop == "onion"
    assert res.language == "hi"

def test_router_english_query():
    res = route_query("What crop to grow now?", default_lang="en")
    assert res.intent == "what_to_grow"
    assert res.language == "en"
