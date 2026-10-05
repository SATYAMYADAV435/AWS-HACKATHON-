# KisanMitra — UI/UX Design Specification (`design.md`)

Design spec and visual language for KisanMitra: a voice-first, low-literacy agricultural assistant built for Indian farmers.

---

## 1. Visual Language & Aesthetic Direction

### "Modern Earth Bohemian" (Agri-Bohemian)

- **Philosophy:** Organic, grounded, tactile, and warm. Designed to immediately feel natural to Indian farmers without falling into generic, soulless "AI SaaS flat" designs or blue/purple tech gradients.
- **Palette:**
  - **Canvas / Background:** `#FAF6EE` (Warm unbleached raw paper / Khadi cotton)
  - **Card Surface:** `#FFFFFF` with warm cream tint (`#FDFCFA`), border in `#E8DEC8`
  - **Primary Earth / Voice Accent:** `#C85A32` (Sun-baked Terracotta Clay)
  - **Secondary Foliage Accent:** `#3B6938` (Deep Farm Sage / Neem green)
  - **Warm Sunlight / Alert Accent:** `#D99B26` (Ochre Yellow / Harvest mustard)
  - **Text & Contrast:** `#1E241E` (Charcoal Slate, avoiding pure harsh black)
- **Shapes & Textures:** Soft, organic pebble contours (`border-radius: 20px - 28px`), subtle jute/khadi weave border treatments, debossed tactile button shadows (`box-shadow: 0 4px 14px rgba(60, 40, 20, 0.08)`).
- **Typography:**
  - Devanagari (Hindi/Marathi): **Baloo 2** (friendly, high legibility) or **Noto Sans Devanagari**.
  - English: **Plus Jakarta Sans** or **Outfit**.
  - Weights: Bold headings and metrics, medium body labels. Minimum body size: 16px.

---

## 2. Global Strict Language State Rule

- **Single-Language Determinism:** The UI must adhere strictly to the chosen language.
  - If **English (`en`)** is selected: 100% of visible UI strings, prompt recommendations, and labels render in English.
  - If **Hindi (`hi`)** is selected: 100% of visible UI strings render in Devanagari Hindi.
  - If **Marathi (`mr`)** is selected: 100% of visible UI strings render in Devanagari Marathi.
- **No Script Mixing:** Never mix Latin and Devanagari characters in a single sentence or card.

---

## 3. Screen Hierarchy & Component Specs (Top to Bottom)

The home dashboard follows a strict, single-column vertical flow optimized for one-hand thumb use on mobile devices (360px–420px viewports):

```text
┌──────────────────────────────────────────────┐
│ [📍 Nashik, Maharashtra ▾]                   │ 1. Location Selector
├──────────────────────────────────────────────┤
│ [ English ] [ हिंदी ] [ मराठी* ] (🔊)         │ 2. Language Segmented Pill
├──────────────────────────────────────────────┤
│                                              │
│                ((( 🎙️ )))                     │ 3. Focused Mic & Wave Rings
│           "बोला, आम्ही ऐकतोय"                 │
│                                              │
├──────────────────────────────────────────────┤
│ [ कांद्याला आज काय भाव आहे? ] [ ⌲ ]         │ 4. Chat Input Bar
├──────────────────────────────────────────────┤
│ 💡 विचारा: [बाजार भाव] [पाऊस कधी?] [पेरणी]   │ 5. Search Recommendations
├──────────────────────────────────────────────┤
│ ┌────────────────────┐ ┌──────────────────┐  │ 6. 2x2 Core Feature Grid
│ │ 🌱 काय पिकवावे?  │ │ 🌦️ आजचे हवामान │  │
│ └────────────────────┘ └──────────────────┘  │
│ ┌────────────────────┐ ┌──────────────────┐  │
│ │ 💰 बाजार भाव      │ │ 📖 शेती सल्ला  │  │
│ └────────────────────┘ └──────────────────┘  │
└──────────────────────────────────────────────┘
```

---

### Component 1: Location Header

- **Position:** Topmost bar, centered or left-aligned with subtle padding.
- **Element:** Rounded woodblock-styled pill containing a pin icon and dropdown arrow.
- **Content:**
  - English: `📍 Nashik, Maharashtra ▾`
  - Hindi: `📍 नाशिक, महाराष्ट्र ▾`
  - Marathi: `📍 नाशिक, महाराष्ट्र ▾`
- **Interaction:** Tapping opens a bottom drawer to switch districts (Nashik, Pune, Solapur, etc.). Modifying this switches regional defaults.

---

### Component 2: Sticky Language Selector

- **Position:** Directly below location.
- **Element:** Segmented toggle with 3 options: `English`, `हिंदी`, and `मराठी` (default regional language for Maharashtra).
- **Behavior:**
  - **Strict Mode:** Switching language immediately switches all UI tokens, button strings, recommendation pills, and speech synthesis engine locales.
  - **Visual State:** The active language sits in a solid terracotta pill (`#C85A32`) with crisp white text. Inactive languages sit on a muted oatmeal tint (`#EFE8D8`) with slate text.
- **Speaker Assist:** A persistent circular speaker button `(🔊)` sits at the far right. Tapping it reads the screen's welcome greeting aloud in the active language.

---

### Component 3: Hero Mic (Centerpiece of the Screen)

- **Dimensions:** Minimum 96px diameter (recommended: 104px).
- **Aesthetic:** Terracotta button (`#C85A32`), matte texture with debossed concentric ring groove lines, centered pure white microphone icon.
- **Animation & Motion Choreography:**
  1. **Idle State:**
     - Gentle rhythmic breathing: scales between `1.0` and `1.04` over 2.8 seconds.
     - Ambient soft shadow pulses from `rgba(200, 90, 50, 0.2)` to `rgba(200, 90, 50, 0.4)`.
  2. **Listening State (On Tap):**
     - Three circular wave rings (`border: 2px solid #C85A32`) emit outward from behind the mic button.
     - *Wave 1:* Expands to 150px (0s delay, opacity fades 0.8 → 0).
     - *Wave 2:* Expands to 210px (0.4s delay, opacity fades 0.6 → 0).
     - *Wave 3:* Expands to 270px (0.8s delay, opacity fades 0.4 → 0).
     - Subtitle below mic switches to: *"ऐकत आहे... (Listening...)"* with a tiny live audio waveform level.
  3. **Heard State:**
     - Mic collapses slightly (`scale(0.95)`), ripples disappear, displays a quick leaf-green confirm ring.
     - Speech-to-text preview surfaces instantly.
  4. **Fallback Handling:** If speech permissions are blocked, the mic displays a slashed-mic icon and a warm informational banner: *"माइक सुरू नाही. खाली लिहून विचारा." (Mic blocked. Type below).*

---

### Component 4: Clean Chat Bar

- **Position:** Below the hero mic.
- **Visual:** High-contrast rounded pill (`border-radius: 28px`), warm paper background (`#FFFFFF`), subtle border (`#D8CEB9`), soft inner shadow.
- **Elements:**
  - Left: Search/chat placeholder text in the selected language:
    - `en`: *"Ask anything about your farm..."*
    - `hi`: *"अपनी खेती के बारे में कुछ भी पूछें..."*
    - `mr`: *"शेतीबद्दल काहीही विचारा..."*
  - Right: Terracotta leaf-shaped submit arrow button `[ ⌲ ]` (active only when text is entered).

---

### Component 5: Recommended Search Prompts (Chips)

- **Position:** Directly underneath the chat bar.
- **Element:** Horizontal scrolling chip carousel with a subtle prefix label: `💡 विचारा (Try asking):`.
- **Visual:** Flat warm stone chips (`#F0EAE1`), rounded borders (`border-radius: 16px`), font size 14px.
- **Content Matrix:**

| Language | Chip 1 (Crop) | Chip 2 (Price) | Chip 3 (Weather) |
|---|---|---|---|
| **English** | "What crop to grow now?" | "Today's onion mandi price" | "Can I spray pesticide today?" |
| **Hindi** | "अभी कौन सी फसल लगाएं?" | "आज प्याज का मंडी भाव" | "क्या आज छिड़काव कर सकते हैं?" |
| **Marathi** | "आता कोणते पीक घ्यावे?" | "कांद्याचा आजचा बाजारभाव" | "आज औषध फवारणी करावी का?" |

- **Interaction:** Tapping any chip immediately fires the router flow as if spoken.

---

### Component 6: 2x2 Core Feature Grid

- **Position:** Bottom section of the home dashboard.
- **Layout:** Compact 2x2 tactile card layout (equal width columns, 12px gap).
- **Card Anatomy:** Large touch targets (min height: 88px), warm off-white surface, bold icon badge on top, single bold label below.
- **Grid Items:**
  1. **Crop Planning:**
     - Icon: 🌱 (Forest Sage Badge)
     - Text: `What to Grow` | `क्या लगाएं?` | `काय पिकवावे?`
  2. **Live Weather:**
     - Icon: 🌦️ (Sky Amber Badge)
     - Text: `Weather Today` | `आज का मौसम` | `आजचे हवामान`
  3. **Mandi Market:**
     - Icon: 💰 (Harvest Ochre Badge)
     - Text: `Mandi Prices` | `बाजार भाव` | `बाजार भाव`
  4. **Crop Guide:**
     - Icon: 📖 (Terracotta Handbook Badge)
     - Text: `How to Grow` | `फसल सलाह` | `लागवड माहिती`

---

## 4. Result Card / Advisory Overlay Specification

When an answer arrives via voice or button selection, it renders an uncluttered Bohemian summary card sliding up from the bottom:

1. **Audio First Bar:** Large persistent player at the top of the card:
   - `[ 🔊 पुन्हा ऐका (Listen Again) ]` with playback animation.
2. **Key Metric Tiles (Max 3):** Three horizontal clay-tinted tags with numbers:
   - e.g., *"अंदाजे उत्पन्न: ₹45,000 / एकर"* (Yield/Income)
   - e.g., *"कालावधी: 110-120 दिवस"* (Duration)
   - e.g., *"बाजार कल: ↗ ₹1,850 / क्विंटल"* (Trend)
3. **Actionable Steps:** Maximum 3 bullet points with rounded terracotta index counters (1, 2, 3).
4. **Mandatory Honesty Tagline:** Grounded footer text:
   - *"स्रोत: महात्मा फुले कृषी विद्यापीठ (MPKV) | प्रातिनिधिक माहिती, अंदाज नाही." (Source cited, indicative only).*
5. **Escape / Contact Action:**
   - Secondary button: `[ 📞 KVK ला कॉल करा (Call KVK) ]`.
   - Primary button: `[ 🎙️ दुसरा प्रश्न विचारा (Ask Another) ]`.

---

## Key Implementation Guidelines for the Coding Agent (RULES.md alignment)

- **CSS Ripple Implementation:** Avoid heavy third-party animation libraries. Implement the circular voice ripples using lightweight CSS keyframe animations (`@keyframes ripple { transform: scale(...); opacity: 0; }`).
- **Devanagari Font Loading:** Include Google Fonts for Baloo 2 (weights: 500, 600, 700) directly in the `<head>` of `frontend/index.html` to prevent layout reflow during vernacular language switching.
- **Clean State Transitions:** In `frontend/app.js`, manage language through a single state dictionary loaded from `frontend/i18n/`, ensuring that switching language re-renders all 6 layout components dynamically without refreshing the page.
