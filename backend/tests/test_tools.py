"""
Tests for backend/tools/ (regions.py, mandi.py, weather_tool.py).
"""

from backend.tools.regions import get_district_info, get_district_coordinates, get_typical_soils
from backend.tools.mandi import get_latest_price, get_price_trend, compare_nearby_mandis
from backend.tools.weather_tool import get_weather_forecast

def test_regions_tool():
    info = get_district_info("nashik")
    assert info is not None
    assert info["id"] == "nashik"
    assert "medium_black" in info["typical_soils"]

    lat, lon = get_district_coordinates("nashik")
    assert abs(lat - 20.0) < 0.1
    assert abs(lon - 73.78) < 0.1

    soils = get_typical_soils("pune")
    assert len(soils) > 0

def test_mandi_tool():
    price_info = get_latest_price("onion", district="nashik")
    assert price_info["commodity"] == "onion"
    assert price_info["modal_price"] > 1000
    assert "market" in price_info

    trend = get_price_trend("onion", days=30)
    assert trend["commodity"] == "onion"
    assert "pct_change" in trend
    assert trend["direction"] in ("up", "down", "stable")

    comparison = compare_nearby_mandis("onion")
    assert len(comparison) >= 2
    assert comparison[0]["modal_price"] >= comparison[1]["modal_price"]

def test_weather_tool():
    w = get_weather_forecast("nashik")
    assert w["district"] == "nashik"
    assert "current" in w
    assert "temperature_c" in w["current"]
    assert "advisory" in w
    assert w["advisory"]["spray_flag"] in ("green", "amber", "red")
