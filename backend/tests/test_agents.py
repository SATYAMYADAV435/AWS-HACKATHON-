"""
Unit tests for backend/agents/ (weather, land, market, crop_guide).
Verifies that all agents return valid AgentResult schemas per ARCHITECTURE.md §3.
"""

from backend.schemas import FarmerProfile, AgentResult
from backend.agents.weather import run_weather_agent
from backend.agents.land import run_land_agent
from backend.agents.market import run_market_agent
from backend.agents.crop_guide import run_crop_guide_agent

def test_all_agents_return_valid_contract():
    profile = FarmerProfile(district="nashik", acres=3.0, water_source="well", language="mr")

    weather_res = run_weather_agent(profile)
    assert isinstance(weather_res, AgentResult)
    assert weather_res.agent == "weather"
    assert weather_res.risk in ("low", "medium", "high")
    assert len(weather_res.evidence) >= 1

    land_res = run_land_agent(profile)
    assert isinstance(land_res, AgentResult)
    assert land_res.agent == "land"
    assert "nashik" in land_res.finding.lower()

    market_res = run_market_agent(profile, crop="onion")
    assert isinstance(market_res, AgentResult)
    assert market_res.agent == "market"
    assert "1850" in market_res.finding or "दर" in market_res.finding

    guide_res = run_crop_guide_agent(profile, crop="onion")
    assert isinstance(guide_res, AgentResult)
    assert guide_res.agent == "crop_guide"
    assert guide_res.data_source in ("s3", "kb")
