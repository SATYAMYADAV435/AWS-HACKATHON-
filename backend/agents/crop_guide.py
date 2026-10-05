"""
KisanMitra — backend/agents/crop_guide.py
Crop guide agent querying ICAR/agri-university package of practices per ARCHITECTURE.md §2 & §5.
"""

import os
from pathlib import Path
from typing import Optional
from backend.schemas import AgentResult, FarmerProfile

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GUIDES_DIR = DATA_DIR / "guides"
KB_MODE = os.environ.get("KB_MODE", "s3").lower()

CROP_GUIDE_MAP = {
    "onion": "onion_rabi_guide.txt",
    "gram": "gram_chickpea_guide.txt",
    "wheat": "wheat_rabi_guide.txt",
    "rabi_jowar": "rabi_jowar_guide.txt",
    "tomato": "tomato_winter_guide.txt",
    "safflower": "safflower_kardi_guide.txt"
}

def run_crop_guide_agent(profile: FarmerProfile, crop: Optional[str] = "onion") -> AgentResult:
    target_crop = (crop or "onion").lower()
    filename = CROP_GUIDE_MAP.get(target_crop)
    guide_file = (GUIDES_DIR / filename) if filename else None

    source_name = "महात्मा फुले कृषी विद्यापीठ (MPKV) राहुरी"
    summary = ""
    evidence = []

    if guide_file and guide_file.exists():
        with open(guide_file, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        for line in lines:
            if line.startswith("SOURCE:"):
                source_name = line.replace("SOURCE:", "").strip()
            elif line.startswith("RECOMMENDED VARIETIES:") or line.startswith("VARIETIES:"):
                evidence.append(line)
            elif line.startswith("ESTIMATED YIELD:"):
                evidence.append(line)

        summary = f"{target_crop.capitalize()} पिकासाठी सुधारित वाणांची निवड आणि शिफारशीत खत व पाणी व्यवस्थापन अत्यंत महत्त्वाचे आहे."
    else:
        # Mandatory fallback sentence per RULES.md §1
        source_name = "कृषी विज्ञान केंद्र (KVK)"
        summary = "प्रमाणित माहिती उपलब्ध नाही. अधिक माहिती व खत/कीटकनाशक प्रमाणासाठी जवळच्या कृषी विज्ञान केंद्राशी (KVK) संपर्क साधा किंवा किसान कॉल सेंटर 1800-180-1551 वर कॉल करा."
        evidence.append("No local university guide on file")

    evidence.append(f"Source Document: {filename}")
    evidence.append(f"Authority: {source_name}")

    return AgentResult(
        agent="crop_guide",
        finding=summary[:400],
        risk="low",
        evidence=evidence[:4],
        data_source="s3",
        next_check="Follow university recommended schedule"
    )
