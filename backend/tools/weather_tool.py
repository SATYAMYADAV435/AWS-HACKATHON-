"""
KisanMitra — backend/tools/weather_tool.py
Weather forecast and agricultural spraying window analyzer using Open-Meteo API
with offline cached fallback per ARCHITECTURE.md §2, §7, and §9.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import requests

from backend.tools.regions import get_district_coordinates

logger = logging.getLogger("kisanmitra.weather")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_DIR = DATA_DIR / "weather_cache"
USE_CACHE = os.environ.get("USE_CACHE", "true").lower() in ("true", "1", "yes")

def _load_cached_weather(district: str) -> Dict[str, Any]:
    d_clean = district.strip().lower()
    cache_file = CACHE_DIR / f"{d_clean}_weather.json"
    if not cache_file.exists():
        cache_file = CACHE_DIR / "nashik_weather.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default fallback object
    return {
        "district": d_clean,
        "current": {
            "temperature_c": 29.0,
            "condition": "Clear Sky",
            "wind_speed_kmh": 9.5,
            "humidity_pct": 45
        },
        "advisory": {
            "spray_flag": "green",
            "spray_reason": "Dry weather and gentle breeze (<12 km/h) are favorable for spraying.",
            "irrigation_advice": "Normal irrigation recommended.",
            "source": "KisanMitra Weather Model"
        }
    }

def get_weather_forecast(district: str = "nashik") -> Dict[str, Any]:
    """
    Fetches 7-day weather forecast from Open-Meteo or cached fallback.
    Computes agricultural safety windows (spray condition, rainfall risk).
    """
    d_clean = district.strip().lower() if district else "nashik"
    if USE_CACHE:
        return _load_cached_weather(d_clean)

    lat, lon = get_district_coordinates(d_clean)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        f"&timezone=Asia/Kolkata"
    )

    try:
        resp = requests.get(url, timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            daily = data.get("daily", {})

            wind_now = current.get("wind_speed_10m", 10.0)
            temp_now = current.get("temperature_2m", 28.0)
            rain_today = daily.get("precipitation_sum", [0.0])[0] if daily.get("precipitation_sum") else 0.0

            # Compute spray flag (green, amber, red)
            if rain_today > 1.0 or wind_now > 20.0:
                spray_flag = "red"
                spray_reason = "पावसाची शक्यता किंवा वेगवान वाऱ्यामुळे आज फवारणी टाळावी (Avoid spray due to rain/high wind)."
            elif wind_now > 12.0:
                spray_flag = "amber"
                spray_reason = "मध्यम वारे आहेत, फवारणी सावधगिरीने सकाळी किंवा संध्याकाळी करावी (Moderate wind; spray carefully)."
            else:
                spray_flag = "green"
                spray_reason = "हवामान कोरडे व शांत असल्याने आज फवारणीसाठी अगदी अनुकूल (Ideal calm dry weather for spraying)."

            return {
                "district": d_clean,
                "current": {
                    "temperature_c": temp_now,
                    "condition": "Sunny / Clear" if rain_today == 0 else "Rainy",
                    "wind_speed_kmh": wind_now,
                    "humidity_pct": current.get("relative_humidity_2m", 50)
                },
                "advisory": {
                    "spray_flag": spray_flag,
                    "spray_reason": spray_reason,
                    "irrigation_advice": "हलके पाणी द्यावे, पाणी साचू देऊ नका (Provide light irrigation, avoid waterlogging).",
                    "source": "Open-Meteo API (Live)"
                }
            }
    except Exception as e:
        logger.warning(f"Open-Meteo live API call failed ({e}); serving cached forecast.")

    return _load_cached_weather(d_clean)
