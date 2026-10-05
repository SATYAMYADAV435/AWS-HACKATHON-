"""
KisanMitra — backend/schemas.py
Pydantic contracts and validators for inter-module payloads per ARCHITECTURE.md §3.
Enforces non-negotiable safety rules: schema validation failure returns a safe fallback, never a crash.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

# Allowed intents per RULES.md §3
IntentType = Literal["what_to_grow", "weather_today", "prices", "how_to_grow", "unknown"]
LanguageType = Literal["en", "hi", "mr", "gu", "pa", "kn", "te", "ta"]
RiskLevel = Literal["low", "medium", "high"]
DataSourceType = Literal["open-meteo", "cache", "csv", "kb", "s3", "regions.json", "mpkv_bulletin"]

# 1. Farmer Profile Contract
class FarmerProfile(BaseModel):
    district: str = Field(default="nashik")
    acres: float = Field(default=3.0, ge=0.1, le=500.0)
    water_source: str = Field(default="well") # well, canal, borewell, rainfed
    language: LanguageType = Field(default="mr")
    season: str = Field(default="rabi")

    # Enhanced Farm Personalization Attributes
    farm_id: Optional[str] = Field(default=None)
    farm_name: Optional[str] = Field(default="Farm 1")
    state: Optional[str] = Field(default="Maharashtra")
    locality: Optional[str] = Field(default="")
    soil_type: Optional[str] = Field(default="medium_black") # medium_black, deep_black, red, alluvial_clay, sandy_loam, shallow_black
    soil_ph: Optional[str] = Field(default="6.8") # e.g. "normal", "acidic", "alkaline", or numeric
    soil_quality: Optional[str] = Field(default="good") # good, medium, degraded, unknown
    irrigation_type: Optional[str] = Field(default="drip") # drip, sprinkler, flood, rainfed
    current_crop: Optional[str] = Field(default=None)
    crop_stage: Optional[str] = Field(default=None) # sowing, vegetative, flowering, fruiting, harvesting, fallow
    notes: Optional[str] = Field(default="")

    @field_validator("district", mode="before")
    @classmethod
    def normalize_district(cls, v: str) -> str:
        return str(v).strip().lower() if v else "nashik"

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        val = str(v).strip().lower() if v else "mr"
        allowed = ("en", "hi", "mr", "gu", "pa", "kn", "te", "ta")
        return val if val in allowed else "mr"

# 2. Router Output Contract
class RouterOutput(BaseModel):
    intent: IntentType = Field(default="what_to_grow")
    crop: Optional[str] = Field(default=None)
    language: LanguageType = Field(default="mr")

    @field_validator("intent", mode="before")
    @classmethod
    def validate_intent(cls, v: str) -> str:
        valid_intents = {"what_to_grow", "weather_today", "prices", "how_to_grow", "unknown"}
        v_str = str(v).strip().lower() if v else "unknown"
        return v_str if v_str in valid_intents else "unknown"

    @field_validator("crop", mode="before")
    @classmethod
    def normalize_crop(cls, v: Optional[str]) -> Optional[str]:
        if not v or v.lower() in ("null", "none", ""):
            return None
        return str(v).strip().lower()

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        val = str(v).strip().lower() if v else "mr"
        allowed = ("en", "hi", "mr", "gu", "pa", "kn", "te", "ta")
        return val if val in allowed else "mr"

# 3. Shared Agent Result Contract (EVERY agent returns exactly this shape)
class AgentResult(BaseModel):
    agent: str = Field(...)
    finding: str = Field(..., max_length=500)
    risk: RiskLevel = Field(default="low")
    evidence: List[str] = Field(default_factory=list)
    data_source: str = Field(default="cache")
    next_check: Optional[str] = Field(default=None)

# 4. Metric Item for Answer Card UI
class MetricItem(BaseModel):
    label: str
    value: str

# 5. Answer Card Contract (Frontend renders and speaks verbatim)
class AnswerCard(BaseModel):
    title: str = Field(...)
    summary_lines: List[str] = Field(..., max_length=3)
    steps: List[str] = Field(default_factory=list, max_length=3)
    labels: List[str] = Field(default_factory=lambda: ["प्रातिनिधिक माहिती", "खर्चापूर्वीचे उत्पन्न"])
    sources: List[str] = Field(default_factory=lambda: ["महात्मा फुले कृषी विद्यापीठ (MPKV)"])
    speak_text: str = Field(...)
    language: LanguageType = Field(default="mr")
    metrics: Optional[List[MetricItem]] = Field(default=None)

    @field_validator("summary_lines", "steps", mode="before")
    @classmethod
    def cap_three_items(cls, v: List[str]) -> List[str]:
        if isinstance(v, list):
            return [str(item) for item in v[:3]]
        return []

# Safe Fallback Builders
def safe_fallback_card(lang: str = "mr", reason: str = "") -> AnswerCard:
    """Safe fallback response whenever any step or schema fails."""
    if lang == "hi":
        return AnswerCard(
            title="सलाहकार सहायता (किसान मित्र)",
            summary_lines=[
                "आपके सवाल की सटीक जानकारी की पुष्टि की जा रही है।",
                "कृपया नीचे दिए गए 4 विकल्पों में से कोई चुनें।",
                "या अपने नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।"
            ],
            steps=[
                "1. मौसम या मंडी भाव बटन दबाकर देखें।",
                "2. सवाल को दोबारा साफ आवाज में बोलें।",
                "3. किसान कॉल सेंटर (1800-180-1551) पर फोन करें।"
            ],
            labels=["सुरक्षित बैकअप", "प्रातिनिधिक"],
            sources=["किसान मित्र सुरक्षा कोर"],
            speak_text="माफ़ करें, जानकारी प्राप्त करने में समय लग रहा है। कृपया नीचे दिए गए बटनों से चयन करें या किसान कॉल सेंटर से संपर्क करें।",
            language="hi"
        )
    elif lang == "en":
        return AnswerCard(
            title="Advisory Support (KisanMitra)",
            summary_lines=[
                "We could not verify this exact query safely.",
                "Please select one of the 4 core feature cards below.",
                "Or call your local Krishi Vigyan Kendra for assistance."
            ],
            steps=[
                "1. Check Weather Today or Mandi Prices directly.",
                "2. Re-speak your question clearly.",
                "3. Contact Kisan Call Centre at 1800-180-1551."
            ],
            labels=["Safe Fallback", "Indicative"],
            sources=["KisanMitra Safety Core"],
            speak_text="We could not verify that query safely. Please tap one of the feature cards or contact the Kisan Call Centre.",
            language="en"
        )
    else: # mr default
        return AnswerCard(
            title="सल्लागार सहाय्य (किसान मित्र)",
            summary_lines=[
                "आपल्या प्रश्नाची खात्रीशीर माहिती तपासली जात आहे.",
                "कृपया खालील ४ प्रमुख पर्यायांपैकी एकावर टॅप करा.",
                "किंवा जवळच्या कृषी विज्ञान केंद्राशी संपर्क साधा."
            ],
            steps=[
                "1. हवामान किंवा बाजार भाव बटण निवडा.",
                "2. प्रश्न पुन्हा एकदा स्पष्ट आवाजात विचारा.",
                "3. किसान कॉल सेंटरवर (1800-180-1551) मोफत कॉल करा."
            ],
            labels=["सुरक्षित बॅकअप", "प्रातिनिधिक"],
            sources=["किसान मित्र सुरक्षा कोर"],
            speak_text="माफ करा, या प्रश्नाची माहिती तपासण्यात अडचण आली. कृपया खालील बटनांवर टॅप करा किंवा किसान कॉल सेंटरशी संपर्क साधा.",
            language="mr"
        )

def validate_answer_card_dict(data: dict, lang: str = "mr") -> dict:
    """Validates dict against AnswerCard schema, returning safe fallback if invalid."""
    try:
        card = AnswerCard(**data)
        return card.model_dump()
    except Exception:
        return safe_fallback_card(lang).model_dump()

# 6. Farm Intelligence Contract
class FarmIntelligenceResponse(BaseModel):
    farm_id: Optional[str] = None
    farm_name: str = "Farm 1"
    district: str = "nashik"
    current_crop: Optional[str] = "onion"
    crop_stage: Optional[str] = "vegetative"
    farm_health_score: int = Field(default=85, ge=0, le=100)
    soil_health_score: int = Field(default=80, ge=0, le=100)
    crop_health_risk: str = "low" # low, moderate, high
    weather_summary: dict = Field(default_factory=dict)
    personalized_recommendations: List[str] = Field(default_factory=list)
    alerts: List[dict] = Field(default_factory=list)
    soil_advice: str = ""
    timestamp: str = ""

# 7. Crop Image Analysis Contract
class CropImageAnalysisResponse(BaseModel):
    crop_name: str = "Crop"
    condition: str = "Healthy"
    risk_level: str = "low" # low, moderate, high
    symptoms: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    confidence_pct: int = Field(default=85, ge=0, le=100)
    disclaimer: str = "Indicative diagnostic advisory based on visible image symptoms. For severe escalation, consult your nearest Krishi Vigyan Kendra (KVK) or Call 1800-180-1551."
    image_url: Optional[str] = None

