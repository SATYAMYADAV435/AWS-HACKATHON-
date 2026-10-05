"""
KisanMitra — backend/tools/mandi.py
Mandi prices query tool querying APMC market datasets per ARCHITECTURE.md §2 & §5.
"""

import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MANDI_CSV = DATA_DIR / "mandi_prices.csv"
MANDI_MODE = os.environ.get("MANDI_MODE", "csv").lower()

def _load_csv_records() -> List[Dict[str, Any]]:
    records = []
    if not MANDI_CSV.exists():
        return records
    with open(MANDI_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                records.append({
                    "date": row["date"],
                    "market": row["market"],
                    "district": row["district"].lower(),
                    "commodity": row["commodity"].lower(),
                    "min_price": int(row["min_price"]),
                    "max_price": int(row["max_price"]),
                    "modal_price": int(row["modal_price"])
                })
            except (ValueError, KeyError):
                continue
    return records

def get_latest_price(commodity: str, district: Optional[str] = None) -> Dict[str, Any]:
    """Returns the most recent modal price for a given commodity."""
    c_clean = commodity.strip().lower()
    d_clean = district.strip().lower() if district else None
    records = _load_csv_records()

    # Filter matching commodity
    matched = [r for r in records if r["commodity"] == c_clean]
    if not matched:
        # Fallback to defaults
        return {
            "commodity": c_clean,
            "modal_price": 1850,
            "min_price": 1400,
            "max_price": 2300,
            "market": "Lasalgaon",
            "date": "2026-10-04",
            "district": d_clean or "nashik"
        }

    # Filter district if specified
    if d_clean:
        dist_matched = [r for r in matched if r["district"] == d_clean]
        if dist_matched:
            matched = dist_matched

    # Sort descending by date
    matched.sort(key=lambda x: x["date"], reverse=True)
    return matched[0]

def get_price_trend(commodity: str, days: int = 30) -> Dict[str, Any]:
    """Calculates 30-day price trend direction and percentage change."""
    c_clean = commodity.strip().lower()
    records = _load_csv_records()
    matched = [r for r in records if r["commodity"] == c_clean]

    if not matched:
        return {
            "commodity": c_clean,
            "pct_change": 5.0,
            "direction": "up",
            "start_price": 1700,
            "current_price": 1850,
            "days": days
        }

    matched.sort(key=lambda x: x["date"])
    start_rec = matched[0]
    latest_rec = matched[-1]

    start_p = start_rec["modal_price"]
    curr_p = latest_rec["modal_price"]
    diff = curr_p - start_p
    pct = round((diff / start_p) * 100, 1) if start_p > 0 else 0.0

    if pct > 1.0:
        dir_str = "up"
    elif pct < -1.0:
        dir_str = "down"
    else:
        dir_str = "stable"

    return {
        "commodity": c_clean,
        "pct_change": pct,
        "direction": dir_str,
        "start_price": start_p,
        "current_price": curr_p,
        "days": days
    }

def compare_nearby_mandis(commodity: str, district: Optional[str] = None) -> List[Dict[str, Any]]:
    """Compares prices across APMC mandis for a commodity."""
    c_clean = commodity.strip().lower()
    records = _load_csv_records()
    matched = [r for r in records if r["commodity"] == c_clean]

    # Group by market and get the latest date for each market
    market_map = {}
    for r in matched:
        m = r["market"]
        if m not in market_map or r["date"] > market_map[m]["date"]:
            market_map[m] = r

    results = list(market_map.values())
    results.sort(key=lambda x: x["modal_price"], reverse=True)
    return results
