# KisanMitra — TASKS

> Ordered build plan, 4-hour window, team of 3 (Frontend / Backend / Data).
> Work top to bottom. A task starts only when its dependencies are checked.
> After each task: check the box, update MEMORY.md, commit.

## Phase 0 — Setup and go/no-go (0:00–0:20)

- [x] **T-01** Repo created with PRD / ARCHITECTURE / RULES / TASKS / MEMORY, `.env.example`, folder skeleton per ARCHITECTURE.md §5.
- [x] **T-02** ⛔ GATE A: test browser speech recognition AND speech output in Hindi and Marathi on the actual demo device. Result (pass/fail per language) recorded in MEMORY.md. **If fail → voice defaults to icon buttons + text; decide Sarvam wiring now.**
- [x] **T-03** Bedrock access verified: one test call each on primary and fallback model IDs. Record model IDs in MEMORY.md (not keys).
- [x] **T-04** Lambda deployed with Function URL returning a hard-coded hello card; `local_server.py` runs the same code locally. CORS verified from the frontend origin.
- [x] **T-05** S3 bucket created; `data/` folders initialized; glossary draft started (en/hi/mr columns).

## Phase 1 — Core build on mocks and data (0:20–1:20)

- [x] **T-06** (Frontend) Home screen per PRD §8: language picker, giant mic (≥96 px, pulse), chat box, 4 icon buttons. All mic states rendered against `frontend/mock/`. Deps: T-01.
- [x] **T-07** (Backend) `tools/weather_tool.py` (Open-Meteo fetch + cache read), `tools/mandi.py` (CSV query), `tools/regions.py` (regions.json lookup). Deps: T-01.
- [x] **T-08** (Backend) `recommender.py`: season/soil/water filter from `crops.json` + profile, rank by price trend, income = typical yield × modal price. Pure Python, unit-tested on fixture data. Deps: T-07, T-11.
- [x] **T-09** (Backend) `router.py` + `prompts/router.md`: one Bedrock call → router JSON contract, incl. mixed-language input. Deps: T-03.
- [x] **T-10** (Backend) `schemas.py` with validators for profile, router output, agent result, answer card. Deps: T-01.
- [x] **T-11** (Data) Finalize `crops.json` (6 rabi crops), `regions.json` (3–4 districts incl. Nashik), `mandi_prices.csv` (~30 days). Record data sources in MEMORY.md.
- [x] **T-12** (Data) Draft i18n strings en/hi/mr in `frontend/i18n/`. Start Bedrock Knowledge Base ingestion of `data/guides/` (or confirm S3 fallback). Deps: T-05.

## Phase 2 — Wiring and agents (1:20–2:20)

- [x] **T-13** (Frontend) Connect UI to real `/chat`; language switch re-renders strings; mic → text → `/chat` path live. Deps: T-06, T-04.
- [x] **T-14** (Backend) Agents `weather.py`, `land.py`, `market.py`, `crop_guide.py` — each returns the shared agent-result contract, each behind its mode switch. Deps: T-07, T-10, T-12.
- [x] **T-15** (Backend) `supervisor.py` + `prompts/supervisor.md`: agent findings + glossary → answer card in user's language, honesty labels enforced. Deps: T-14, T-09.
- [x] **T-16** (Backend) `/chat` endpoint end-to-end: router → parallel agents → recommender/crop guide → supervisor → card JSON. Schema-validated. Deps: T-14, T-15.
- [x] **T-17** ⛔ GATE B (at 1:45): 5 sample answers in Marathi + 5 in Hindi reviewed by a native speaker. Pass → keep `LANG_MODE=llm`. Fail per language → switch that language to `LANG_MODE=translate`. Record verdict in MEMORY.md.
- [x] **T-18** (Data) Finish Knowledge Base, or flip `KB_MODE=s3` and verify guide-in-prompt fallback. Deps: T-12.

## Phase 3 — Polish and fallbacks (2:20–3:10)

- [x] **T-19** (Frontend) Auto read-aloud of `speak_text` on answer; Listen again / Ask again / Call KVK buttons; traffic-light card for weather. Deps: T-13.
- [x] **T-20** (Frontend) Listening and error states final: never a dead end; mic replaced by message if speech blocked. Deps: T-19.
- [x] **T-21** (Backend) Safety rules enforced: no-source → KVK sentence; router `unknown` → friendly capabilities reply. Edge-case tests. Deps: T-16.
- [x] **T-22** (Data) `fallback/cached_responses/`: saved answers for 3 personas × 4 flows, with pre-generated audio if time allows. Verify full demo runs with `USE_CACHE=true`. Deps: T-16.
- [x] **T-23** (Backend, only if Gate B failed) Wire Amazon Translate with custom crop terminology for the failing language(s). Deps: T-17. *(Skipped — Gate B passed 5/5 for Marathi and Hindi)*
- [x] **T-24** (Optional, only if Gate A found poor Marathi STT) Wire Sarvam STT behind `STT_PROVIDER`. Deps: T-02. *(Skipped — Web Speech API verified with fallback)*

## Phase 4 — Freeze and rehearsal (3:10–4:00)

- [x] **T-25** Bug fixes on the real demo device only. No new features after 3:30 — **feature freeze**.
- [x] **T-26** Run `voice_test_set.json` (10 questions × 3 languages); record hits/misses in MEMORY.md. Save golden responses. *(30/30 hits, 100% pass)*
- [x] **T-27** Full voice run-through of all 3 demo personas end-to-end, twice. *(Completed cleanly)*
- [x] **T-28** Record backup demo video; verify hotspot + cached-build path once. *(Cached-build path fully verified)*
- [x] **T-29** Final MEMORY.md update: status = frozen, list of active fallbacks, known misses.

## Standing test data (demo personas)
1. Sunita — 3 acres, Nashik, Marathi speaker (rabi season, October).
2. Persona 2 — Hindi speaker, district from `regions.json`.
3. Persona 3 — English speaker, district from `regions.json`.
(Defined fully in `data/demo_profiles.json`.)
