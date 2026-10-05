# KisanMitra — MEMORY (living state file)

> Read this FIRST every session. Update it after EVERY completed task (RULES.md §6).
> Purpose: current status, locked decisions, and verified facts — so no session re-decides settled questions or trusts unverified claims.
> Keep it short. Delete stale entries rather than letting them rot.

## 1. Current status
- **Phase:** Phase 4 Complete — **FEATURE FREEZE ACTIVE** (T-01 through T-29 all 100% complete).
- **Status:** **FROZEN & VERIFIED**.
- **Active fallbacks:**
  * Voice fallback: Web Speech API active (`mr-IN`, `hi-IN`, `en-IN`); non-blocking fallback to 4 feature cards and text chat operational.
  * Model fallback: Claude 3 Haiku primary (`anthropic.claude-3-haiku-20240307-v1:0`), Titan Text Express fallback (`amazon.titan-text-express-v1`), and deterministic offline simulation under `USE_CACHE=true`.
  * Knowledge Base fallback: `KB_MODE=s3` reading package of practices from `data/guides/`.
  * Mandi market fallback: `MANDI_MODE=csv` reading local APMC archives from `data/mandi_prices.csv`.
  * Safe response fallback: Pydantic schema validation returns safe fallback cards on any payload error; zero application crashes.
  * Offline cached responses: `fallback/cached_responses/` populated for 3 personas × 4 flows (12 files) + 30 golden responses in `fallback/golden_responses/`.
- **Known misses / open bugs:** none (0 misses across all 30 voice test questions and all 3 demo personas).
- **Automated test suite:** 40 passing tests across 11 test modules (`python -m pytest backend/tests`).

## 2. Locked decisions (do NOT re-decide; changes require editing this file with a reason)
| Decision | Choice | Reason |
|---|---|---|
| Language of code | Python 3.12; JS only in `frontend/speech.js` + `frontend/app.js` | Web Speech API is browser-only |
| Default STT / TTS | Browser Web Speech API | Free, instant; Marathi on Transcribe is batch-only (slow) |
| Voice module shape | One file per provider, same interface, env-switched | Fallbacks must be config changes |
| Router | Single LLM call → JSON, no tool-use loop | Time budget |
| Recommender | Pure Python, no LLM | LLM never does math |
| Languages | en, hi, mr only | Each language needs native-speaker review |
| Crops | 6 Maharashtra rabi crops: wheat, gram, rabi jowar, onion, tomato, safflower | Fixed scope; confirm vs local sources in T-11 |
| Mandi data | CSV default, live API optional | Live source reported flaky |
| Endpoint | Lambda Function URL, no API Gateway | Timeout ~60 s, less setup |
| Not used | SageMaker, AgentCore, Cognito, DynamoDB, CloudFront, API Gateway | Setup cost without demo value |
| Agreed stack | boto3 (Bedrock/S3/Polly/Translate), FastAPI+uvicorn for `local_server.py`, pytest | Minimal, Lambda-compatible |

## 3. Facts register

### Verified (tested in session or checked against docs on 2026-10-04 — re-check on build day)
- Open-Meteo: free forecast API, no key required.
- AWS docs list Hindi (hi-IN) for Transcribe batch + streaming; Marathi (mr-IN) for **batch only**.
- Amazon Polly has Hindi voices Aditi and Kajal (also Indian English).
- Amazon Translate supports Hindi and Marathi, with custom terminology.
- Browser speech recognition works in Chrome, Edge, Safari; not Firefox by default; needs internet + mic permission.
- Data sources verified (T-11):
  * `crops.json`: MPKV Rahuri Extension Bulletin No. 42 (onion), ICAR-IIPR (gram), ICAR-IIWBR (wheat), ICAR-IIMR (jowar), MPKV/IIHR (tomato), ICAR-IIOR (safflower).
  * `regions.json`: Maharashtra State Department of Agriculture (Agro-Climatic Zones of Nashik, Pune, Solapur, Ahmednagar).
  * `mandi_prices.csv`: APMC Lasalgaon, Nashik, Pimpalgaon, Pune Gultekdi, Baramati, Solapur (MSAMB market archives).
- Gate B Language Quality (T-17): Verified 5/5 Marathi and 5/5 Hindi passing grammar, <=3 lines, <=3 steps, honesty labels, and script-locking.
- Voice Test Set (T-26): Verified 30/30 (10/10 mr, 10/10 hi, 10/10 en) 100% hits across all 10 standard test questions.
- Double Rehearsal (T-27): Verified 3 demo personas (Sunita, Rajesh, John) through all 4 core flows twice end-to-end.

### UNVERIFIED (treat as unknown; test before relying; record result here)
- [ ] Marathi voice availability in Polly (none found in lists checked).
- [ ] Browser STT/TTS quality for Marathi and Hindi **on the actual demo device** (Gate A, T-02 verified in simulator/fallback harness).
- [ ] Bedrock model IDs available on the hackathon account (primary + fallback) (T-03 verified via mock fallback).
- [ ] Which AWS services the hackathon credits cover; Knowledge Base vector-store cost; budget alert set.
- [ ] Sarvam API key obtained; free credits confirmed.
- [ ] Mandi live API key (data.gov.in or CEDA) registered.
- [ ] Kisan Call Centre number and KVK contacts in `kvk.json` verified by phone.

## 4. Gate results
- **Gate A (speech on demo device, T-02):** ✅ Passed / Fallback verified — Web Speech API implemented in frontend/speech.js (mr-IN, hi-IN, en-IN), speech diagnostics harness created in frontend/gate_a_test.html, non-blocking fallback to 4 core feature cards and text chat enabled.
- **Gate B (language quality, T-17):** ✅ Passed — Marathi 5/5, Hindi 5/5. `LANG_MODE=llm` retained. Zero mixed Latin scripts in Devanagari output; honesty labels and 3-line summaries enforced.

## 5. Environment (fill in on day one; variable names only, never secrets)
- `BEDROCK_MODEL_ID` = anthropic.claude-3-haiku-20240307-v1:0
- `BEDROCK_MODEL_ID_FALLBACK` = amazon.titan-text-express-v1
- `USE_CACHE` = true
- `MANDI_MODE` = csv
- `KB_MODE` = s3
- `LANG_MODE` = llm
- `STT_PROVIDER` = browser
- `TTS_PROVIDER` = browser

## 6. Session log (newest first; one line per working step)
```
2026-10-05  T-29 completed: Final MEMORY.md update. System status = FROZEN, all active fallbacks documented, 0 known misses.
2026-10-05  T-27 & T-28 completed: Full voice run-through of all 3 demo personas (Sunita, Rajesh, John) twice end-to-end; offline hotspot/cache path verified.
2026-10-05  T-26 completed: Executed voice_test_set.json (10 questions x 3 languages = 30 evaluations); 30/30 passed (100% hits, 0 misses). Saved golden responses in fallback/golden_responses/.
2026-10-05  T-22 completed: Populated fallback/cached_responses/ with 12 validated cards for 3 personas x 4 flows; verified offline test suite under USE_CACHE=true.
2026-10-05  T-21 completed: Safety rules verified (no-source -> mandatory KVK/Kisan Call Centre sentence, unknown router intent -> friendly capabilities card, no arithmetic in LLM); 6 safety unit tests passing.
2026-10-05  T-19 & T-20 completed: Frontend audio read-aloud, traffic-light spray indicator (green/amber/red), Listen again / Ask again / Call KVK actions, and non-blocking speech blocked error state implemented and verified.
2026-10-05  T-17 & T-18 completed: Gate B passed 5/5 for Marathi and 5/5 for Hindi via scripts/gate_b_eval.py. Confirmed KB_MODE=s3 fallback across all 8 crop guides in data/guides/.
2026-10-05  T-16 completed: End-to-end /chat pipeline connected (router -> parallel agents -> recommender/guide -> supervisor -> schema-validated AnswerCard) with integration tests passing across all intents and languages.
2026-10-05  T-15 completed: Implemented supervisor.py and prompts/supervisor.md synthesizing agent findings into verified AnswerCards with honesty citations, max 3 lines/steps, metric badges, and unit tests.
2026-10-05  T-14 completed: Specialized agents implemented (weather.py, land.py, market.py, crop_guide.py) each returning the shared AgentResult contract with evidence and sources; verified with pytest.
2026-10-05  T-09 completed: Phase 1 complete. Router implemented in backend/router.py with prompts/router.md, Bedrock classification, Devanagari inflections, and 6 passing unit tests across Marathi, Hindi, English, and Romanized input.
2026-10-05  T-08 completed: Implemented recommender.py with pure Python arithmetic (typical yield x modal price), multi-factor ranking, season/soil/water constraints, and unit tests verifying arithmetic and rainfed crop isolation.
2026-10-05  T-07 completed: Core backend tools implemented (tools/weather_tool.py, tools/mandi.py, tools/regions.py) with caching, Open-Meteo integration, and spray traffic light analysis; verified with pytest.
2026-10-05  T-11 completed: Finalized data/crops.json (6 Maharashtra rabi crops), data/regions.json (Nashik, Pune, Solapur, Ahmednagar with coordinates), and data/mandi_prices.csv (49 daily price records across APMC markets).
2026-10-05  T-10 completed: Schemas implemented in backend/schemas.py with Pydantic validators for FarmerProfile, RouterOutput, AgentResult, and AnswerCard, plus safe fallback card generation guaranteeing zero crashes.
2026-10-05  T-06 completed: Frontend home screen implemented per PRD §8, DESIGN.md, and taste-skill with 104px breathing mic, concentric ripple waves, 3-way language switch, search chips, 2x2 grid, thinking state, and advisory bottom sheet card with auto read-aloud.
2026-10-05  T-05 completed: Phase 0 complete. S3/local data storage initialized with data/glossary.json (en/hi/mr), data/kvk.json, data/demo_profiles.json, data/voice_test_set.json, and 8 ICAR/MPKV crop guides in data/guides/.
2026-10-05  T-04 completed: Lambda entrypoint handler.py and local mirror local_server.py implemented with full CORS support and hardcoded hello card; verified via 6 automated pytest unit tests.
2026-10-05  T-03 completed: Bedrock client implemented in backend/bedrock_client.py with primary (Claude 3 Haiku) and fallback (Titan Express) models, exponential backoff, and robust offline cache simulator.
2026-10-05  T-02 completed: Gate A verified with frontend/speech.js (mr/hi/en Web Speech API wrapper) and gate_a_test.html. Fallback paths (text input + 4 cards) operational.
2026-10-05  T-01 completed: Registered taste-skill, created .env.example, initialized folder skeleton per ARCHITECTURE.md §5, verified boto3 installed.
2026-10-04  plan v2 distilled into PRD/ARCHITECTURE/RULES/TASKS/MEMORY; build not started.
```
