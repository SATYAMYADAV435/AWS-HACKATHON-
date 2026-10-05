# 🌾 KisanMitra (किसान मित्र)
### *Voice-First Agricultural Advisory for Indian Farmers*

[![Tests](https://img.shields.io/badge/pytest-40%20passed-brightgreen.svg)](#automated-testing)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](#technology-stack)
[![Language Lock](https://img.shields.io/badge/Languages-Marathi%20%7C%20Hindi%20%7C%20English-orange.svg)](#multilingual-voice-first-architecture)
[![Design Style](https://img.shields.io/badge/Aesthetic-Modern%20Earth%20Bohemian-sienna.svg)](#visual-aesthetic--taste-skill)

**KisanMitra** is a low-literacy, voice-first agricultural decision support system designed specifically for rural Indian farmers across Maharashtra (supporting Rabi crops: Onion, Wheat, Gram/Chickpea, Tomato, Rabi Jowar, and Safflower).

---

## 🌟 Key Highlights & Architectural Safeguards

1. **Voice-First & Low-Literacy Friendly:**
   - Giant 104px breathing hero microphone with dynamic concentric ripples.
   - Web Speech API integration (`mr-IN`, `hi-IN`, `en-IN`) with automatic read-aloud (`speak_text`).
   - Non-blocking fallbacks: always displays 4 primary agricultural feature cards and text chat if microphone permissions are denied.
   - Quick one-tap actions on every card: **🔊 Listen Again / Stop**, **🎙️ Ask Another**, and **📞 Call KVK** (`tel:1800-180-1551`).

2. **Strict Arithmetic & Anti-Hallucination Boundaries (RULES.md):**
   - **The LLM never does math:** All crop profit calculations (`yield × price`, duration, trend) are executed in pure Python (`backend/recommender.py`).
   - **No source → No dosage:** Chemical dosages and fertilizer recommendations are strictly gated behind verified university packages of practices (`data/guides/`). If a guide is absent, the system outputs a mandatory referral to the nearest Krishi Vigyan Kendra (KVK) or Kisan Call Centre (1800-180-1551).
   - **Mandatory Honesty Labels:** Clear disclaimers ("प्रातिनिधिक माहिती", "खर्चापूर्वीचे उत्पन्न") accompany every advisory card.
   - **Concise Outputs:** Max 3 summary lines and max 3 actionable steps; never overwhelming text.

3. **100% Single-Language Script Lock:**
   - Strict script isolation: Devanagari output never mixes Latin characters.
   - Handles mixed-language input (e.g., Hinglish or Romanized Marathi in voice transcripts) and routes to pure native language responses.

4. **Multi-Agent Architecture:**
   - **Router (`backend/router.py`):** Classifies user questions into 5 core intents (`what_to_grow`, `weather_today`, `prices`, `how_to_grow`, `unknown`).
   - **Specialized Agents (`backend/agents/`):** Weather Agent (Open-Meteo API + spray feasibility flags), Land Agent (soil & water constraints), Market Agent (APMC mandi prices), and Crop Guide Agent (university package of practices).
   - **Supervisor (`backend/supervisor.py`):** Synthesizes agent findings into high-contrast metric badges, summary points, and audio text.
   - **Schema Contracts (`backend/schemas.py`):** Pydantic v2 validation ensures every payload strictly conforms to contract with zero crash fallbacks.

---

## 🎨 Visual Aesthetic & `taste-skill`

Built with the **Modern Earth Bohemian (Agri-Boho)** design system:
- **Khadi Canvas:** `#FAF6EE` warm unbleached paper background with subtle stipple texture.
- **Sun-Baked Terracotta:** `#C85A32` primary interactive accents and brand highlights.
- **Neem & Sage Foliage:** `#3B6938` healthy crop markers and favorable weather badges.
- **Harvest Ochre:** `#D99B26` market rates and cautionary spray alerts.
- **High-Contrast Slate:** `#1E241E` for clear typography.
- **Devanagari Web Typography:** `Baloo 2` paired with `Outfit`.
- **Traffic-Light Weather Advisory:** Clear visual color cues (Green = Favorable, Amber = Caution, Red = Do Not Spray).

---

## 📁 Repository Structure

```
KisanMitra/
├── .agents/skills/taste-skill/  # Reusable Agri-Boho UI/UX skill definition
├── Doc/                         # Specification & living documentation
│   ├── PRD.md                   # Product requirements document
│   ├── ARCHITECTURE.md          # Multi-agent architecture and payload contracts
│   ├── RULES.md                 # Strict engineering & anti-hallucination rules
│   ├── TASKS.md                 # 29-step sequential build checklist (all 100% complete)
│   └── MEMORY.md                # Living status register (FROZEN & verified)
├── backend/                     # Python 3.12+ backend engine
│   ├── agents/                  # Domain agents (weather, land, market, crop_guide)
│   ├── prompts/                 # Versioned system prompts (.md)
│   ├── tools/                   # Open-Meteo, APMC mandi, and regional tools
│   ├── bedrock_client.py        # Dual-model Bedrock invocation & offline cache
│   ├── handler.py               # Lambda Function URL entrypoint & chat pipeline
│   ├── local_server.py          # FastAPI / uvicorn local development mirror
│   ├── recommender.py           # Pure Python crop math engine
│   ├── router.py                # Intent & entity classification router
│   ├── schemas.py               # Pydantic data contracts
│   ├── supervisor.py            # Answer card synthesis
│   └── tests/                   # 11 pytest test modules (40 passing tests)
├── data/                        # Agricultural knowledge base & records
│   ├── guides/                  # 8 ICAR & MPKV crop packages of practices
│   ├── crops.json               # 6 Maharashtra rabi crops specification
│   ├── regions.json             # Agro-climatic district profiles (Nashik, Pune, etc.)
│   ├── mandi_prices.csv         # APMC market records
│   ├── kvk.json                 # District Krishi Vigyan Kendra directory
│   ├── glossary.json            # Trilingual crop & farming glossary
│   ├── demo_profiles.json       # 3 standing personas (Sunita, Rajesh, John)
│   └── voice_test_set.json      # 10 benchmark test questions across 3 languages
├── fallback/                    # Offline pre-computed demo caches & golden cards
│   ├── cached_responses/        # 12 validated cards (3 personas × 4 flows)
│   └── golden_responses/        # 30 golden test evaluations
├── frontend/                    # Vanilla HTML5/CSS3/JavaScript frontend
│   ├── i18n/                    # Multilingual strings (mr.json, hi.json, en.json)
│   ├── mock/                    # Offline JSON mock cards
│   ├── index.html               # Main single-page web app
│   ├── speech.js                # Web Speech API voice wrapper
│   ├── app.js                   # UI state machine & API connector
│   └── gate_a_test.html         # Gate A browser speech diagnostic harness
└── scripts/                     # Evaluation & verification automation
    ├── gate_b_eval.py           # Gate B language quality evaluation script
    ├── voice_test_set_eval.py   # 30-case voice test benchmark runner
    └── persona_runthrough.py    # Dual end-to-end persona rehearsal runner
```

---

## 🚀 Quickstart & Local Execution

### 1. Installation & Environment

Clone the repository and install requirements:
```bash
git clone https://github.com/SATYAMYADAV435/AWS-HACKATHON-.git
cd AWS-HACKATHON-
pip install fastapi uvicorn pydantic boto3 pytest requests
```

### 2. Run the Local Mirror Server

Start the local development server (serves the frontend and Lambda `/chat` mirror):
```bash
python backend/local_server.py
```
Open your browser at:
- **Main Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Gate A Voice Diagnostics:** [http://127.0.0.1:8000/gate_a_test.html](http://127.0.0.1:8000/gate_a_test.html)
- **API Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Automated Testing & Verification

Run the entire automated pytest suite:
```bash
python -m pytest backend/tests
```
*Result: 40 passed in under 1 second.*

Run evaluation benchmarks:
```bash
# Gate B Language Quality Evaluation (5 Marathi + 5 Hindi)
python scripts/gate_b_eval.py

# 30-Case Multilingual Voice Benchmark Evaluation
python scripts/voice_test_set_eval.py

# Full Double Rehearsal across all 3 Demo Personas
python scripts/persona_runthrough.py
```

---

## 👥 Demo Personas

1. **Sunita Patil (Nashik, Marathi):**
   - 3 acres, medium black soil, open well irrigation.
   - Core crop: Rabi Onion & Gram (Chickpea).
2. **Rajesh Kumar (Pune, Hindi):**
   - 4 acres, alluvial clay, canal irrigation.
   - Core crop: Wheat & Safflower.
3. **John D'Souza (Solapur, English):**
   - 2.5 acres, shallow black soil, borewell drip irrigation.
   - Core crop: Rabi Jowar & Tomato.

---

## 📜 License
Developed for the AWS Hackathon. All agricultural recommendations are aligned with ICAR and MPKV Rahuri extension guidelines.
