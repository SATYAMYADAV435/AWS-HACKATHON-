---
name: taste-skill
description: Visual, UI, styling, and animation decisions for KisanMitra using the Modern Earth Bohemian (Agri-Boho) aesthetic for rural Indian farmers.
---

# KisanMitra Taste Skill: Modern Earth Bohemian (Agri-Boho)

## 1. Visual Aesthetic & Philosophy
- **Style Direction:** Modern Earth Bohemian / Agri-Boho.
- **Audience:** Indian farmers, designed for clarity, respect, tactile familiarity, and low literacy.
- **Strict Avoidance:** Generic corporate AI gradients, flat SaaS templates, neon tech motifs, purple glows, pure black (`#000000`).
- **Tactile Materiality:** Warm unbleached paper / khadi canvas (`#FAF6EE`), sun-baked terracotta clay accents (`#C85A32`), deep farm sage / neem foliage (`#3B6938`), and harvest ochre mustard (`#D99B26`). Card surfaces in warm cream (`#FDFCFA` with `#FFFFFF` base) bordered by soft earthy jute tone (`#E8DEC8`).
- **Text & Contrast:** Charcoal Slate (`#1E241E`) providing sharp contrast (WCAG AAA) on light earthy surfaces.

## 2. Typography & Accessibility
- **Devanagari (Marathi / Hindi):** `Baloo 2` (warm, rounded, highly legible) and `Noto Sans Devanagari`.
- **English:** `Outfit` / `Plus Jakarta Sans`.
- **Weights & Sizes:** Minimum body text: 16px. Section headings: bold, 20px–24px. Hero mic status: 22px–28px bold.
- **Touch Target Rule:** Every primary button and touch target must be at least 56px in height/width (Hero mic is ≥ 96px, ideally 104px).

## 3. Strict Language Determinism
- **100% Single-Language Lock:** When English is selected, 100% of visible UI strings render in English. When Hindi is selected, 100% render in Hindi (Devanagari). When Marathi is selected, 100% render in Marathi (Devanagari).
- **Zero Script Mixing:** Never mix Latin and Devanagari in the same sentence or card.

## 4. Micro-Interactions & Pure CSS Animation
- **Hero Mic States:**
  1. *Idle:* Organic gentle breathing pulse scaling between `1.0` and `1.04` over 2.8s with soft terracotta ambient shadow.
  2. *Listening:* Three concentric circular wave rings radiating outward from behind the mic (`@keyframes ripple`) with delays (0s, 0.4s, 0.8s) expanding to 150px, 210px, 270px and fading smoothly.
  3. *Heard:* Quick scale to `0.95`, leaf-green confirm ring, transition into auto-send progress countdown (1.5s).
  4. *Thinking:* Dynamic tribal-inspired pulsating status badges (Weather, Soil, Mandi).
- **Result Bottom-Sheet & Cards:**
  - Slide up with smooth cubic-bezier easing (`cubic-bezier(0.16, 1, 0.3, 1)`).
  - Prominent audio scrubber `[ 🔊 Listen Again ]`.
  - Max 3 key metric badges (clay tinted).
  - Max 3 concise numbered actionable steps.
  - Clear honesty citation taglines.
