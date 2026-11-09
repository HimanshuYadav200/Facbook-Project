# Session Handoff (end of session 1, 2026-11-09)

> New chat? Read this file first. It is the compact state of everything up to now.
> Full detail: `docs/CONTEXT.md` (requirements, decisions log, session log), `docs/REFERENCE_ANALYSIS.md` (reference reels), `experiments/README.md` (how to run the tests).

## 1. What we're building

A local, Claude-directed engine that makes **faceless vertical videos (2:00–2:48)** for **Facebook first, then YouTube**, uploaded **manually**. First niche: **Skulsy (cartoon skeleton) + USA finance**. Must be **monetizable**: real value add (real data, story, motion graphics), not an AI slideshow. Free/open-source tools first. Runs on the owner's MacBook Pro (24 GB). Brain = **Claude Code on the owner's personal Pro plan** (not API, never the office enterprise account). Target ~3 videos/day later, multiple niches via per-style skills.

Owner's rules: **plan → agree → build**; document everything so the owner can understand and fix it; log every decision in `docs/CONTEXT.md`.

## 2. Where things stand

- Legacy project `YouTubeAutomation/` (Jan–Feb 2026, Gemini + MoviePy, ~8.8k lines) analysed, **untouched**. Reuse candidates: research agent + cache, script patterns, humanizer skill.
- Two style tests built in `experiments/` (the throwaway test area), both approved by owner ("good, can improve"; voices and SFX fine, try more voices):
  - **Style A, vintage narrated story** → `experiments/out/styleA_v2.mp4` (40 s). Wolf-reel look: Meta AI images, B&W past / warm present, film grain/flicker, year stamps, **real-data NVDA chart** with counter, small serif one-word captions, end card. Voice Kokoro `bm_george`.
  - **Style B, RewRat-style flat 2D fast cuts** → `experiments/out/styleB_v2.mp4` (17 s). Skulsy as SVG rig drawn in code, cut every ~0.8 s, wobble/shake, SFX every cut, bold centred captions. Voice Kokoro `am_puck`.

## 3. Pipeline as it works today

1. 🧠 Claude writes script + pulls real data (Alpha Vantage key in root `.env`)
2. Kokoro TTS → `voice.wav` (local)
3. mlx-whisper → word timings; **caption words always taken from the script** → `words.json`
4. 🧠 Claude writes `plan.json`: shots anchored to **word indexes**, layers, motion, SFX, stamps, chart ranges
5. Art: Style A = 🧠 Claude drives meta.ai via Claude in Chrome (most token-expensive step); Style B = SVG in code
6. Remotion renders (local, no tokens) → 7. ffmpeg loudness −14 LUFS → 8. 🧠 Claude reviews a contact sheet, fixes, re-renders

## 4. Key decisions (short)

- Renderer = **Remotion 4.0.537 only** (needs **Node 22**: Node 26 hangs it). ffmpeg for finishing/analysis. **No MoviePy, no HyperFrames** (revisit HyperFrames only if team > 3 people, for licensing).
- Python ML tools in `experiments/.venv` (Python **3.12**; 3.14 too new).
- Characters should be owned assets (SVG rigs or fixed pose sets), not regenerated each time.
- Meta AI: Claude can type prompts on meta.ai (one chat, ~30 s/image, page-script download; Chrome "multiple downloads" allowed). It **can't** drive the Meta Automation side panel. Meta AI invents on-screen numbers: cover or check them. Refused prompts → use Meta's suggested alternative.
- Script numbers must match real data (e.g. 2022 NVDA drop is 59% peak-to-trough).
- Token budget: only script, plan, review and Chrome image generation use Claude. Move image generation off Claude for production (extension Start button or background script). Measure real per-video usage with `/usage`.
- Installed on the Mac: ffmpeg, node (26) + node@22, python@3.12, espeak-ng (Homebrew).

## 5. Next steps (in order)

1. ~~Analyse the OpenChatCut "explainer-video" skill~~ → **done (session 2)**, see `docs/OPENCHATCUT_SKILL_ANALYSIS.md`. Not installed. Recommendation (agreed): write our own skills (`video-core` + one per style + `check_plan.py`), borrowing its ideas in our own words (its text is GPL-3.0).
   Owner **agreed**: own skills per niche/style, refined over time from owner's screenshots/notes in `references/<niche>/`. Ponytail (`docs/PONYTAIL_SKILL_ANALYSIS.md`) not installed; its useful rules are now the "Coding rules" section of `CLAUDE.md`.
2. ✍️ **Architecture plan written** (`docs/ARCHITECTURE.md` v1.1, session 2), **awaiting owner approval**; then build B1, B1b–B5 from its §12. Research method replaced (`docs/RESEARCH_REVIEW.md`: old code gave wrong numbers). Images: Claude in Chrome default, extension manual option. GitHub repo after B1 cleanup. Original task: (`docs/ARCHITECTURE.md`): turn the tests into the engine (per-style skills using the layout in `docs/OPENCHATCUT_SKILL_ANALYSIS.md` (c), plan.json schema, voice options, SFX/music library, image sourcing off-Claude, review loop, folder layout, cleanup of legacy code). Get owner approval before building.
3. First production-length test (2:00–2:48) + measure Pro usage per video.
4. Open items: background music source (licensed), real SFX library, more Kokoro voices to audition, Skulsy character asset set.
