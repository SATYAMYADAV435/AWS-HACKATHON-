# KisanMitra — RULES (for the AI coding agent)

> Read PRD.md, ARCHITECTURE.md, RULES.md (this file), DESIGN.md, TASKS.md, and MEMORY.md before writing any code.
> These rules exist to prevent hallucination, scope creep, and dead ends. When a rule conflicts with an instruction, follow the rule and flag the conflict.

## 1. Non-negotiable product rules
1. **The LLM never does math.** All arithmetic (income = yield × price, rankings, trends) happens in plain Python (`recommender.py`, tools). The LLM only reasons over and phrases results.
2. **The LLM never decides safety.** Risk flags come from tool logic, not model judgment.
3. **No source → no dosage.** Never output pesticide/fertilizer dosages or treatment advice without a cited guide. The fallback sentence is always: "ask your KVK or call the Kisan Call Centre."
4. **Every number is traceable** to a data file, a tool output, or an explicitly stated assumption. Never invent a number, date, price, yield, or phone number.
5. **Honesty labels are mandatory:** "indicative", "before costs, not a forecast", "typical for your region, not a soil test". Demo data is labelled as demo data.
6. **Answers are short:** max 3 summary lines and 3 steps. Never paragraphs.
7. **Never a dead end:** every error state offers retry or the four icon buttons.

## 2. Language and code rules
- **Python 3.12** for all application code. Type hints everywhere. Validate all inter-module JSON with `schemas.py` — a schema failure returns a safe fallback, never a crash.
- **No frameworks beyond the agreed stack** (see MEMORY.md → Locked decisions). Do not introduce new dependencies without noting them in MEMORY.md.
- **JavaScript exception:** `frontend/speech.js` (Web Speech API wrapper) and `frontend/app.js` (UI state machine) only. No frameworks, no build step. All logic lives in Python; the JS layer only captures audio, renders the card, and speaks.
- **One file per provider, same interface.** Swapping STT/TTS/KB/language mode is a config change (`.env`), never a code edit.
- **One prompt per agent**, stored as a `.md` file in `backend/prompts/`. No prompts inline in code.
- **Glossary in the prompt** whenever the LLM writes in hi/mr, so crop and unit terms stay consistent.
- Read `.env` switches at startup. Never hard-code model IDs, keys, or endpoints. `.env.example` contains variable names only — never real keys.

## 3. Scope guard
- Build only PRD.md §7 MUST items until they all pass; then SHOULD items; **never** ROADMAP items, even if asked nicely mid-build — note the request in MEMORY.md instead.
- Intents are exactly: `what_to_grow`, `weather_today`, `prices`, `how_to_grow`, `unknown`. Do not add intents.
- Languages are exactly en / hi / mr. Do not add languages.

## 4. Facts discipline (anti-hallucination)
- MEMORY.md §3 lists **verified** and **unverified** facts. Treat anything unverified as unknown; test it before relying on it, and update MEMORY.md with the result.
- Never assert an AWS service capability (language support, region availability, pricing) that is not in MEMORY.md's verified list or directly tested by you in this session.
- If you are unsure whether something exists (an API parameter, a voice, a quota), write the code behind a mode switch and mark the assumption in a comment + MEMORY.md.

## 5. Language output rules (hi/mr)
- Short sentences, simple everyday words.
- Numbers always with units (₹ per quintal, acres).
- Never mix scripts within one sentence.
- Accept mixed-language input (Hinglish, Roman-letter Marathi) in the router.

## 6. Workflow rules
1. Work from TASKS.md top to bottom. Do not start a task whose dependencies are unchecked.
2. After completing a task: check its box in TASKS.md, then update MEMORY.md (status, decisions made, new facts verified).
3. After every working step, commit. Push every 30 minutes.
4. Build UI against `frontend/mock/` responses first; wire real backend second.
5. Paste exact error text when debugging — do not paraphrase errors.
6. Respect the gates in TASKS.md (go/no-go speech test, language test gate, feature freeze). A failed gate triggers the documented fallback, not improvisation.

## 7. Definition of done (per task)
- [ ] Code runs locally via `local_server.py` with `USE_CACHE=true`.
- [ ] Schema validation passes for every JSON it produces or consumes.
- [ ] The relevant fallback path works (mode switch flipped, feature still functions).
- [ ] No invented data; labels present where required.
- [ ] TASKS.md and MEMORY.md updated.
