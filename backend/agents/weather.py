"""
KisanMitra — backend/agents/weather.py
Weather agent returning shared AgentResult contract per ARCHITECTURE.md §2 & §3.
"""

from typing import Optional
from backend.schemas import AgentResult, FarmerProfile
from backend.tools.weather_tool import get_weather_forecast

def run_weather_agent(profile: FarmerProfile, crop: Optional[str] = None) -> AgentResult:
    district = profile.district or "nashik"
    forecast = get_weather_forecast(district)

    advisory = forecast.get("advisory", {})
    current = forecast.get("current", {})
    spray_flag = advisory.get("spray_flag", "green")

    # Map spray flag to risk level
    risk_map = {"green": "low", "amber": "medium", "red": "high"}
    risk = risk_map.get(spray_flag, "low")

    temp = current.get("temperature_c", 28.0)
    wind = current.get("wind_speed_kmh", 10.0)
    source = advisory.get("source", "open-meteo")
    data_source = "open-meteo" if "Live" in source else "cache"

    finding = f"{advisory.get('spray_reason', 'हवामान अनुकूल आहे.')} {advisory.get('irrigation_advice', '')}".strip()

    evidence = [
        f"District: {district.capitalize()}",
        f"Current Temp: {temp}°C",
        f"Wind Speed: {wind} km/h",
        f"Spray Condition: {spray_flag.upper()}"
    ]

    return AgentResult(
        agent="weather",
        finding=finding[:400],
        risk=risk,
        evidence=evidence,
        data_source=data_source,
        next_check="Check again in 24 hours"
    )
