# KisanMitra — PRD

Voice-first, multilingual farm assistant on AWS. Hackathon build window: 4 hours.

> AI agent read order: PRD.md → ARCHITECTURE.md → RULES.md → DESIGN.md → TASKS.md → MEMORY.md
> This file defines WHAT to build. Not how. If anything conflicts with this file, stop and flag it.

## 1. One-liner
A farmer taps a big mic and asks in their own language. A team of AI agents checks weather, region and soil, crop guidance, and current mandi prices, then answers in a short spoken and written card.

## 2. Problem
- Farmers need answers to: what should I grow now, how do I grow it, what is the weather doing, what are prices like. This information sits in different places.
- Many farmers cannot read or type comfortably. Reading/typing-first apps exclude them.

## 3. Target user
- Small and medium farmers, starting with Maharashtra.
- Languages: Marathi (`mr`), Hindi (`hi`), English (`en`). Exactly these three — no more in this build.
- May not read well. Must be able to speak a question and hear the answer.

## 4. Goals
1. Working end-to-end demo: voice question in → spoken + written answer out, about 20 seconds.
2. AWS doing real work: Bedrock, Lambda, S3, Knowledge Base.
3. Every number comes from a tool, a data file, or a stated assumption. Every how-to comes from a cited source.

## 5. Non-goals (never build, never imply)
- Not a diagnosis tool. Not a pesticide prescriber. Not a price forecaster. Not a profit guarantee.

## 6. Design principles
1. **Agents reason. Tools compute. Rules verify.** The LLM never does the math, never decides safety, and never gives treatment advice without a source.
2. **Voice first, text second.** The whole journey must work without reading: speak, hear, tap icons.
3. **Short answers.** Max 3 reasons and 3 steps, never paragraphs.
4. **Honest by default.** Use "indicative", "typical for your region", "ask your KVK". Demo data is labelled as demo data.
5. **Every dependency has a fallback.** Cached data, a local runner, and mode switches (see ARCHITECTURE.md §7).
6. **Demo first.** The UI works on mock JSON before any AWS wiring.

## 7. Scope

### MUST (in scope)
- First screen: big mic, chat box, and 4 icon buttons (grow, weather, prices, how to grow).
- Voice question → router → existing flow → answer card → automatic read-aloud.
- Setup: district, acres, water source, language.
- `what_to_grow`: top 3 crops with indicative income per acre, before costs.
- `how_to_grow [crop]`: steps, inputs, schedule, with sources.
- `prices`: current price and 30-day trend.
- `weather_today`: today's work flagged green / amber / red.
- en / hi / mr with reviewed UI strings and a crop glossary.

### SHOULD (build only after MUST works)
- Bedrock Knowledge Base for crop guides (S3 fallback ready).
- Lite "best nearby mandi" comparison from the CSV.
- Second voice provider (Sarvam, or Amazon Polly for Hindi) wired as a fallback.

### ROADMAP (do NOT build — pitch only)
- Plant photo check, SMS and WhatsApp alerts, offline mode, login, more languages, price forecasting, FPO dashboard, insurance and lending links.

## 8. First screen spec
Goal: a farmer who cannot read gets an answer within three taps.

Layout, top to bottom:
1. **Language picker** — each language written in its own script, plus a speaker button that says the welcome out loud.
2. **Giant mic button** — at least 96 px, high contrast, gentle pulse, small label and icon. The main thing on screen.
3. **Chat box** with send button, for people who prefer typing.
4. **Four icon buttons** — grow, weather, prices, how to grow. Each has a picture, one word, and a spoken label on long-press.

Mic states:

| State | Behavior |
|---|---|
| Idle | Pulsing mic. If the browser blocks speech, the mic is replaced by a clear message; icon buttons stay active. |
| Listening | Tap once to start. Big animated rings, "listening" label. Stops on silence or second tap. |
| Heard | Recognised text appears in large type with a Cancel button. Auto-sends after ~1.5 s. |
| Thinking | Animated icons for weather, land, prices. Takes 10–20 s; keep it lively. |
| Answer | Short card, **read aloud automatically**. Buttons: Listen again, Ask another question, Call the KVK. |
| Error | "I could not hear that." Try again, or tap an icon button. Never a dead end. |

Browsers block audio until the user taps something — acceptable, because the farmer taps the mic first.

## 9. Voice pipeline
1. **Speech to text:** browser speech recognition in the chosen language (default provider).
2. **Router:** ONE LLM call returns JSON `{intent, crop, language}`. Intents: `what_to_grow`, `weather_today`, `prices`, `how_to_grow`, `unknown`.
3. **Existing flow runs** — the same guided flow as the matching button. Voice adds no new backend logic.
4. **Unknown intent:** friendly reply listing what the app can do, plus the four buttons.
5. **Text to speech:** the final card is read aloud in the same language (browser default provider).

Mixed-language input (Hinglish, Marathi in Roman letters or Devanagari) must route correctly.

## 10. Languages
- **Fixed UI text:** reviewed i18n files for en / hi / mr.
- **Dynamic text:** the LLM writes in the user's language, with the glossary in its prompt.
- **Fallback:** agents write grounded English → Amazon Translate converts (mode switch `LANG_MODE`, see ARCHITECTURE.md §7).
- **Writing rules:** short sentences, simple everyday words, numbers always with units (₹ per quintal, acres), never mix scripts in one sentence.
- Adding a language later = one i18n file + one glossary column + one speech code. No code changes.

## 11. Acceptance criteria
- [ ] All four flows work end-to-end by voice in all three languages.
- [ ] Answer appears in ≤ 20 s and is read aloud automatically.
- [ ] Every number is traceable to a data file or tool; every how-to has a named source.
- [ ] Usable with zero reading ability (voice + icons only).
- [ ] With AWS unreachable, the demo still runs from cache (`USE_CACHE=true`).
- [ ] Voice pipeline degraded gracefully: if speech fails, buttons and text box carry the full demo.
