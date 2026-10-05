"""
KisanMitra — backend/tools/regions.py
Region, soil, and climate profile lookup tool per ARCHITECTURE.md §2 & §5.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REGIONS_FILE = DATA_DIR / "regions.json"

_regions_cache: Optional[Dict[str, Any]] = None

def _load_regions() -> Dict[str, Any]:
    global _regions_cache
    if _regions_cache is not None:
        return _regions_cache
    if not REGIONS_FILE.exists():
        return {"districts": []}
    with open(REGIONS_FILE, "r", encoding="utf-8") as f:
        _regions_cache = json.load(f)
    return _regions_cache

def get_all_districts() -> List[Dict[str, Any]]:
    data = _load_regions()
    return data.get("districts", [])

def get_district_info(district_name: str) -> Optional[Dict[str, Any]]:
    if not district_name:
        return None
    d_clean = district_name.strip().lower()
    districts = get_all_districts()
    for d in districts:
        if d.get("id") == d_clean:
            return d
        name_obj = d.get("name", {})
        if any(str(v).lower() == d_clean for v in name_obj.values()):
            return d
    # Default to nashik if not found
    for d in districts:
        if d.get("id") == "nashik":
            return d
    return None

def get_district_coordinates(district_name: str = "nashik") -> Tuple[float, float]:
    info = get_district_info(district_name)
    if info and "coordinates" in info:
        coords = info["coordinates"]
        return float(coords.get("latitude", 20.0)), float(coords.get("longitude", 73.78))
    return 20.0, 73.78 # Default Nashik

def get_typical_soils(district_name: str = "nashik") -> List[str]:
    info = get_district_info(district_name)
    if info:
        return info.get("typical_soils", ["medium_black"])
    return ["medium_black"]

def get_state_languages() -> Dict[str, Dict[str, str]]:
    data = _load_regions()
    return data.get("state_languages", {})

def get_language_for_state(state: str) -> Dict[str, str]:
    langs = get_state_languages()
    for s_name, l_info in langs.items():
        if s_name.lower() == (state or "").strip().lower():
            return l_info
    return {"code": "mr", "label": "मराठी", "speechCode": "mr-IN"}

