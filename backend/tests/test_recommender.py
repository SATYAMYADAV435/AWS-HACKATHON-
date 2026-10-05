"""
Unit tests for backend/recommender.py verifying arithmetic and filtering rules.
"""

from backend.schemas import FarmerProfile
from backend.recommender import recommend_crops

def test_recommender_arithmetic():
    profile = FarmerProfile(district="nashik", acres=3.0, water_source="well", language="mr")
    result = recommend_crops(profile)

    assert "recommended_crops" in result
    crops = result["recommended_crops"]
    assert len(crops) <= 3
    assert len(crops) > 0

    for c in crops:
        yield_val = c["typical_yield_quintal_per_acre"]
        price_val = c["modal_price_per_quintal"]
        expected_gross = int(round(yield_val * price_val))
        assert c["gross_income_per_acre"] == expected_gross
        assert c["total_indicative_gross_income"] == expected_gross * 3

def test_recommender_rainfed_filtering():
    # Rainfed farmer should not receive high-water crops like wheat
    profile = FarmerProfile(district="solapur", acres=2.0, water_source="rainfed", language="mr")
    result = recommend_crops(profile)
    crop_ids = [c["crop_id"] for c in result["recommended_crops"]]
    assert "wheat" not in crop_ids
    # Low-water crops like gram, rabi_jowar, safflower should appear
    assert any(c in crop_ids for c in ["gram", "rabi_jowar", "safflower"])
