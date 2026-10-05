"""
KisanMitra — backend/recommender.py
Pure Python crop recommendation and income arithmetic engine per PRD §6, ARCHITECTURE.md §2, and RULES.md §1.
CRITICAL: The LLM NEVER does math. All filtering, calculations, and rankings happen strictly here.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.schemas import FarmerProfile
from backend.tools.mandi import get_latest_price, get_price_trend
from backend.tools.regions import get_typical_soils

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CROPS_FILE = DATA_DIR / "crops.json"

def _load_crops() -> List[Dict[str, Any]]:
    if not CROPS_FILE.exists():
        return []
    with open(CROPS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def recommend_crops(profile: FarmerProfile) -> Dict[str, Any]:
    """
    Ranks crops based on farmer's profile, season, water availability, and APMC price trends.
    Arithmetic:
    - gross_income_per_acre = typical_yield_quintal × modal_price_per_quintal
    - net_income_per_acre = gross_income_per_acre - cost_of_cultivation_per_acre
    - total_indicative_income = gross_income_per_acre × acres
    """
    crops = _load_crops()
    district_soils = get_typical_soils(profile.district)
    water_source = profile.water_source.lower()
    season = profile.season.lower()
    acres = profile.acres

    candidates = []

    for crop in crops:
        crop_id = crop["id"]
        # 1. Season filter
        if crop.get("season", "rabi").lower() != season:
            continue

        # 2. Water source filter
        allowed_water = [w.lower() for w in crop.get("water_sources_allowed", [])]
        if water_source not in allowed_water and allowed_water:
            # If farmer is rainfed and crop needs high irrigation, exclude
            if water_source == "rainfed" and crop.get("water_need") == "high":
                continue

        # 3. Soil compatibility score
        crop_soils = crop.get("soil_pref", [])
        soil_match = any(s in crop_soils for s in district_soils)

        # 4. Fetch Mandi price and trend
        price_info = get_latest_price(crop_id, profile.district)
        trend_info = get_price_trend(crop_id)

        modal_price = price_info.get("modal_price", 1500)
        yield_data = crop.get("typical_yield_quintal_per_acre", {"typical": 10.0, "min": 8.0, "max": 12.0})
        typical_yield = float(yield_data.get("typical", 10.0))
        cost_per_acre = float(crop.get("cost_of_cultivation_per_acre", 20000))

        # PURE PYTHON ARITHMETIC (RULES.md §1)
        gross_per_acre = int(round(typical_yield * modal_price))
        net_per_acre = int(round(gross_per_acre - cost_per_acre))
        total_gross = int(round(gross_per_acre * acres))

        # Ranking score: gross income + trend bonus + soil bonus
        score = gross_per_acre
        if trend_info.get("direction") == "up":
            score *= 1.10
        elif trend_info.get("direction") == "down":
            score *= 0.90
        if soil_match:
            score *= 1.05

        candidates.append({
            "crop_id": crop_id,
            "name": crop.get("name", {}),
            "modal_price_per_quintal": modal_price,
            "market_name": price_info.get("market", "APMC"),
            "typical_yield_quintal_per_acre": typical_yield,
            "duration_days": crop.get("duration_days", {"min": 100, "max": 120}),
            "gross_income_per_acre": gross_per_acre,
            "net_income_per_acre": net_per_acre,
            "total_indicative_gross_income": total_gross,
            "acres": acres,
            "price_trend": trend_info,
            "soil_compatible": soil_match,
            "source": crop.get("source", "MPKV Rahuri"),
            "varieties": crop.get("varieties", []),
            "ranking_score": score
        })

    # Sort descending by ranking score
    candidates.sort(key=lambda x: x["ranking_score"], reverse=True)
    top_crops = candidates[:3]

    return {
        "district": profile.district,
        "season": season,
        "acres": acres,
        "water_source": water_source,
        "recommended_crops": top_crops,
        "honesty_label": "indicative only, before costs, not a profit forecast",
        "data_sources": ["MPKV Rahuri Bulletins", "MSAMB Mandi Price Archives", "Open-Meteo Weather"]
    }
