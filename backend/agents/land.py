"""
KisanMitra — backend/agents/land.py
Land & region agent returning shared AgentResult contract per ARCHITECTURE.md §2 & §3.
"""

from typing import Optional
from backend.schemas import AgentResult, FarmerProfile
from backend.tools.regions import get_district_info

def run_land_agent(profile: FarmerProfile, crop: Optional[str] = None) -> AgentResult:
    district = profile.district or "nashik"
    info = get_district_info(district)

    if not info:
        return AgentResult(
            agent="land",
            finding=f"जमिनीचा प्रकार मध्यम काळी असून रब्बी हंगामासाठी उपयुक्त आहे.",
            risk="low",
            evidence=[f"District: {district}"],
            data_source="regions.json",
            next_check=None
        )

    soils = ", ".join(info.get("typical_soils", ["medium_black"]))
    rainfall = info.get("annual_rainfall_mm", 700)
    zone = info.get("climate_zone", "Transition Zone")

    finding = (
        f"{district.capitalize()} भागातील जमीन मुख्यतः {soils} स्वरूपाची असून सरासरी पाऊस {rainfall} मिमी आहे. "
        f"ही जमीन रब्बी हंगामातील पिकांसाठी उपयुक्त आहे (हे प्रातिनिधिक विश्लेषण आहे, सॉईल टेस्ट नाही)."
    )

    evidence = [
        f"District: {district.capitalize()}",
        f"Climate Zone: {zone}",
        f"Typical Soils: {soils}",
        f"Annual Rainfall: {rainfall} mm"
    ]

    return AgentResult(
        agent="land",
        finding=finding[:400],
        risk="low",
        evidence=evidence,
        data_source="regions.json",
        next_check=None
    )
