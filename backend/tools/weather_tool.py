"""
KisanMitra — backend/tools/weather_tool.py
Live weather forecast, soil temperature, and agricultural advisory analyzer
using Open-Meteo API (hourly=temperature_2m,soil_temperature_0cm) with
high-resilience offline cached fallback per ARCHITECTURE.md §2, §7, and §9.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from backend.tools.regions import get_district_coordinates

logger = logging.getLogger("kisanmitra.weather")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_DIR = DATA_DIR / "weather_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Default to Live Open-Meteo first; set USE_CACHE=true only to force offline mode
USE_CACHE = os.environ.get("USE_CACHE", "false").lower() in ("true", "1", "yes")

WMO_WEATHER_CODES = {
    0: ("Clear sky", "स्वच्छ आकाश", "साफ आसमान"),
    1: ("Mainly clear", "मुख्यतः निरभ्र", "मुख्य रूप से साफ"),
    2: ("Partly cloudy", "अंशतः ढगाळ", "आंशिक बादल"),
    3: ("Overcast", "पूर्ण ढगाळ", "बादल छाए रहेंगे"),
    45: ("Foggy", "धुके", "कोहरा"),
    48: ("Depositing rime fog", "दाट धुके", "घना कोहरा"),
    51: ("Light drizzle", "हलकी रिमझिम", "हल्की बूंदाबांदी"),
    53: ("Moderate drizzle", "रिमझिम पाऊस", "मध्यम बूंदाबांदी"),
    55: ("Dense drizzle", "जोरदार रिमझिम", "तेज बूंदाबांदी"),
    61: ("Slight rain", "हलका पाऊस", "हल्की बारिश"),
    63: ("Moderate rain", "मध्यम पाऊस", "मध्यम बारिश"),
    65: ("Heavy rain", "मुसळधार पाऊस", "भारी बारिश"),
    71: ("Slight frost / snow", "हलके दव / पाला", "पाला / हल्की बर्फ"),
    80: ("Slight rain showers", "पावसाच्या हलक्या सरी", "हल्की बारिश की बौछारें"),
    81: ("Moderate rain showers", "पावसाच्या मध्यम सरी", "मध्यम बौछारें"),
    82: ("Violent rain showers", "जोरदार पावसाच्या सरी", "तेज बौछारें"),
    95: ("Thunderstorm", "विजांसह वादळी पाऊस", "आंधी-तूफान के साथ बारिश"),
}

def _get_wmo_description(code: int, lang: str = "mr") -> str:
    entry = WMO_WEATHER_CODES.get(code, ("Fair weather", "अनुकूल हवामान", "अनुकूल मौसम"))
    if lang == "hi":
        return entry[2]
    elif lang == "en":
        return entry[0]
    return entry[1]

def _load_cached_weather(district: str) -> Dict[str, Any]:
    d_clean = district.strip().lower()
    cache_file = CACHE_DIR / f"{d_clean}_weather.json"
    if not cache_file.exists():
        cache_file = CACHE_DIR / "nashik_weather.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["district"] = d_clean
                return data
        except Exception as e:
            logger.warning(f"Error reading cache file {cache_file}: {e}")

    # Baseline fallback object if cache file missing
    return {
        "district": d_clean,
        "current": {
            "temperature_c": 28.5,
            "soil_temperature_0cm": 24.0,
            "condition": "Clear Sky / स्वच्छ आकाश",
            "wind_speed_kmh": 9.5,
            "humidity_pct": 50,
            "apparent_temperature_c": 29.0
        },
        "forecast_7d": [],
        "advisory": {
            "spray_flag": "green",
            "spray_reason": "हवामान कोरडे व शांत असल्याने आज फवारणीसाठी अनुकूल आहे (Calm dry weather for spraying).",
            "soil_advice": "मातीचे तापमान (24°C) बियाणे उगवणीसाठी अनुकूल आहे (Soil temp favorable for germination).",
            "irrigation_advice": "नियमित हलके पाणी द्यावे (Provide regular light irrigation).",
            "source": "KisanMitra Weather Model (Cached Fallback)"
        }
    }

def _save_cached_weather(district: str, data: Dict[str, Any]) -> None:
    try:
        cache_file = CACHE_DIR / f"{district}_weather.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"Unable to write weather cache for {district}: {e}")

def get_weather_forecast(district: str = "nashik") -> Dict[str, Any]:
    """
    Fetches live weather & soil temperature forecast from Open-Meteo API
    (hourly=temperature_2m,soil_temperature_0cm) with cached fallback.
    Computes agricultural safety windows (spray condition, soil sowing feasibility, irrigation).
    """
    d_clean = district.strip().lower() if district else "nashik"
    if os.environ.get("USE_CACHE", "false").lower() in ("true", "1", "yes"):
        return _load_cached_weather(d_clean)

    lat, lon = get_district_coordinates(d_clean)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,soil_temperature_0cm,relative_humidity_2m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weather_code"
        f"&timezone=Asia%2FKolkata"
    )

    try:
        resp = requests.get(url, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})

            wind_now = float(current.get("wind_speed_10m", 8.0))
            temp_now = float(current.get("temperature_2m", 28.0))
            humidity_now = int(current.get("relative_humidity_2m", 50))
            apparent_temp = float(current.get("apparent_temperature", temp_now))
            weather_code = int(current.get("weather_code", 0))

            # Soil temperature at 0cm (surface layer crucial for seed germination & seedling vigor)
            soil_temps = hourly.get("soil_temperature_0cm", [])
            soil_temp_now = float(soil_temps[0]) if soil_temps else round(temp_now - 1.5, 1)

            # Daily precipitation for today
            rain_today = 0.0
            if daily.get("precipitation_sum"):
                rain_today = float(daily["precipitation_sum"][0])

            # 1. Compute Spray Flag (green / amber / red)
            if rain_today > 1.0 or wind_now > 20.0:
                spray_flag = "red"
                spray_reason = "पावसाची शक्यता किंवा वेगवान वाऱ्यामुळे (>20 km/h) आज औषध फवारणी टाळावी (Avoid spray due to rain or strong wind)."
            elif wind_now > 12.0:
                spray_flag = "amber"
                spray_reason = "मध्यम वारे (12-20 km/h) आहेत; फवारणी सावधगिरीने सकाळी किंवा संध्याकाळी शांत वेळी करावी (Moderate wind; spray during calm morning/evening)."
            else:
                spray_flag = "green"
                spray_reason = "हवामान कोरडे व वारे शांत (<12 km/h) असल्याने आज फवारणीसाठी अगदी उत्तम वेळ आहे (Ideal calm dry weather for spraying)."

            # 2. Compute Soil Condition & Sowing Advisory based on soil_temperature_0cm
            if 18.0 <= soil_temp_now <= 30.0:
                soil_advice = f"मातीचे पृष्ठभाग तापमान {soil_temp_now}°C आहे — बियाणे पेरणी, अंकुरण व मुळांच्या वाढीसाठी अगदी अनुकूल आहे (Optimal soil temp for sowing)."
            elif soil_temp_now < 18.0:
                soil_advice = f"माती थंड ({soil_temp_now}°C) आहे — पेरणी उबदार सकाळच्या वेळेस करावी (Soil is cool; sow during warm morning hours)."
            else:
                soil_advice = f"मातीचे तापमान अधिक ({soil_temp_now}°C) आहे — जमिनीत ओलावा टिकवण्यासाठी सेंद्रिय आच्छादन (mulching) वापरावे (Soil warm; mulch to preserve moisture)."

            # 3. Compute Irrigation Advice
            if rain_today > 5.0:
                irrigation_advice = "आज पुरेसा पाऊस अपेक्षित असल्याने पाणी देणे पुढे ढकलावे (Rain expected, postpone irrigation)."
            elif humidity_now < 40 and temp_now > 30.0:
                irrigation_advice = "कमी आर्द्रता व उष्णतेमुळे हलके सिंचन करावे, तुषार किंवा ठिबक वापरावे (Low humidity; provide drip irrigation)."
            else:
                irrigation_advice = "जमिनीतील ओलावा तपासून नियमित अंतराने हलके पाणी द्यावे (Provide standard light irrigation)."

            condition_desc = _get_wmo_description(weather_code, "mr")

            # 4. Build 7-day forecast summary
            forecast_7d: List[Dict[str, Any]] = []
            daily_times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            rains = daily.get("precipitation_sum", [])
            winds = daily.get("wind_speed_10m_max", [])
            codes = daily.get("weather_code", [])

            for i in range(min(7, len(daily_times))):
                forecast_7d.append({
                    "day": f"Day {i+1}",
                    "date": daily_times[i],
                    "temp_max": max_temps[i] if i < len(max_temps) else temp_now,
                    "temp_min": min_temps[i] if i < len(min_temps) else temp_now - 8,
                    "rain_mm": rains[i] if i < len(rains) else 0.0,
                    "wind_max_kmh": winds[i] if i < len(winds) else wind_now,
                    "condition": _get_wmo_description(codes[i] if i < len(codes) else 0, "en")
                })

            result = {
                "district": d_clean,
                "latitude": lat,
                "longitude": lon,
                "current": {
                    "temperature_c": temp_now,
                    "apparent_temperature_c": apparent_temp,
                    "soil_temperature_0cm": soil_temp_now,
                    "condition": condition_desc,
                    "condition_en": _get_wmo_description(weather_code, "en"),
                    "condition_hi": _get_wmo_description(weather_code, "hi"),
                    "wind_speed_kmh": wind_now,
                    "humidity_pct": humidity_now,
                    "precipitation_mm": rain_today
                },
                "forecast_7d": forecast_7d,
                "advisory": {
                    "spray_flag": spray_flag,
                    "spray_reason": spray_reason,
                    "soil_advice": soil_advice,
                    "irrigation_advice": irrigation_advice,
                    "source": "Open-Meteo API (Live)"
                }
            }

            # Cache the successful live result
            _save_cached_weather(d_clean, result)
            return result
    except Exception as e:
        logger.warning(f"Open-Meteo live API call failed for {d_clean} ({e}); serving cached fallback.")

    return _load_cached_weather(d_clean)
