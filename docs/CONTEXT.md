# Project Context Log

> Running memory of this project. Every decision, requirement and change from our conversations is recorded here.
> If a chat session resets, read this file first, then `docs/ARCHITECTURE.md`.
> Newest entries go at the bottom of each section. Dates are absolute.

---

## 1. Project goal (as stated by owner, 2026-11-09)

Build an **automated faceless video engine** that produces engaging, *monetizable* videos for Facebook and YouTube, starting with the **Skulsy finance niche**, then expanding to other niches through configuration.

- **First platform:** Facebook. Same video also posted to YouTube.
- **Format:** vertical (9:16), **3–4 minutes**.
- **Upload:** manual by the owner (no upload APIs).
- **Brain:** Claude is the primary LLM. It doesn't just pass data from stage to stage: it plans, reviews and iterates at each stage.
- **Execution:** everything runs locally on the owner's MacBook Pro (24 GB unified memory), with all editing tools installed locally (Remotion, FFmpeg, Blender, etc.), instead of a cloud sandbox.
- **Prefer open source / free:** Kokoro TTS, Google Cloud $300 trial credits for images, Meta AI (free) for images/video via a bulk browser extension.

## 2. Why the project was paused, and what must change

- Paused in Feb 2026 because YouTube was demonetizing AI channels.
- Owner's observation: unmonetized AI channels are slideshows: AI images or clips stitched together + generic AI script + AI voiceover + burned-in captions.
- **Hard requirement:** strictly follow YouTube and Facebook originality / monetization guidelines. Every video must add value for the viewer (original analysis, real data, a story, edited motion graphics), not be a slideshow.

## 3. Quality bar for the edit (owner's requirements)

1. Fast pace, more cuts.
2. Captions, audio and visuals tightly synced.
3. **Sound effects at cuts and transitions that match the scene's theme** (a main priority).
4. No static slideshow: each image gets scene-appropriate motion (Remotion), beyond Ken Burns zoom.
5. Use every useful tool: charts inserted at the right moments, Blender 3D when needed, HyperFrames, motion graphics, background music, MCP integrations.
6. Should look human-edited.
7. Must generalize to any niche. Per-niche style is decided from **reference screenshots** the owner will provide of videos that are already performing.

## 4. Working agreements

- **Plan everything first; change code only after both agree on the plan.**
- Owner must understand every part of the system: `docs/ARCHITECTURE.md` will describe the full flow in detail (what each part does, inputs/outputs, how to fix it) plus a change log of important changes and **why** they were made.
- This file (`docs/CONTEXT.md`) records every new decision from conversations.

## 5. Legacy system summary (state as of Feb 13, 2026)

- Location: `YouTubeAutomation/`, ~8.8k lines of Python, entrypoint `main.py` (1,367 lines, two modes).
- **Default mode (long-form, 16:9):** Research → Script → fact-check → SEO → per-sentence audio → visual grouper → image prompts → images → SFX → MoviePy assembly.
- **Skulsy mode (shorts, 9:16):** pattern-based script (8 patterns in `.agent/skills/script_patterns/`) + quality-score regeneration loop → TTS → Whisk/Grok prompts (manual) → MoviePy assembly.
- Stack: Gemini 3 Pro (text), Imagen 4 / Gemini Flash Image, Google TTS / ElevenLabs, Whisper word timings, MoviePy, research APIs (FRED, Alpha Vantage, Tavily, Serper, NewsAPI) with SQLite cache, Reddit fetcher.
- Keep / reuse candidates: research agent + cache, script patterns & BASE_VIRAL_STRUCTURE, humanizer skill, sentence-level sync idea, script quality loop.
- Known problems: monolithic `main.py`, manual steps (Grok/Whisk, folder polling, `input()`), finance/Skulsy hardcoded, providers hardcoded, resolution hardcoded, regex-only quality checks, no git, no real tests, 4.3 GB media inside source folder, `YouTubeAutomation/` is read-only (`dr-xr-xr-x`).

## 6. Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-11-09 | Start with Skulsy finance, vertical, 3–4 min, Facebook first then YouTube | Owner's plan; high-RPM niche with existing assets |
| 2026-11-09 | Manual upload, no platform APIs | Owner preference |
| 2026-11-09 | Claude = primary brain; local Mac execution | Owner preference; newer LLM editing/motion-graphics ability |
| 2026-11-09 | Open-source first (Kokoro TTS etc.) | Cost |
| 2026-11-09 | Plan-before-code; maintain CONTEXT.md + ARCHITECTURE.md | Owner must understand and be able to fix everything |
| 2026-11-09 | Brain = Claude Code on owner's **personal Pro subscription**; Claude orchestrates locally installed tools (not a cloud sandbox) | Tools run locally at zero token cost; Claude only plans, writes and reviews. Keep design able to switch to API key or Max plan if limits are tight |
| 2026-11-09 | Token budget control: visual review uses one contact-sheet image per pass and a capped number of fix/re-render rounds | Image review is the main token cost |
| 2026-11-09 | Video length **2:00–2:48** (vertical) | Stays under YouTube Shorts' 3-min cap; same file works for Facebook |
| 2026-11-09 | Office/enterprise Claude account is **not** used for this project in any form | Would breach employer policy and account terms |
| 2026-11-09 | Format = **niche bending** of a wolf-explains-to-pig channel (companies / country history) → Skulsy + sidekick explaining **USA finance**. Owner will provide reference videos (in `references/<name>/`) + detailed style breakdown; Claude extracts frames and builds a style profile | Proven high-view format; copy the format, not the identity (own characters, names, look) |
| 2026-11-09 | Meta AI "Meta Automation" extension judged **feasible** as a semi-automatic image/clip source: engine writes prompt batch → owner presses Start → extension downloads to `runs/<video>/incoming/` → engine matches files to shots + Claude contact-sheet check | No GCP credits yet; free bulk generation. Final adoption decided after the style is locked |
| 2026-11-09 | Characters (Skulsy + sidekick) planned as **fixed 2D character assets composited in Remotion**; AI generators make only scenes/backgrounds | AI generators can't keep a character consistent across many shots; owned characters also strengthen originality |
| 2026-11-09 | Two reference styles analysed (see `docs/REFERENCE_ANALYSIS.md`): **A** = vintage mentor/fool story (wolf+pig, 1:55, ~2 s shots, AI image-to-video, one-word serif captions, multi-voice, ambience); **B** = RewRat flat 2D fast-cut (0:28, 0.95 s shots, shake, one-word centered captions, SFX every cut) | Owner wants to test many niches/styles and scale whichever matches booming channels to ~3 reels/day |
| 2026-11-09 | Per-style **Claude skills** (built from screenshots + measured numbers + component library) are the way to encode each style | Owner's idea; matches how creators use Claude for consistent 2D animation |
| 2026-11-09 | Style A adapted to **single-narrator story** ("Skulsy invested $X in Y in year Z…") in the wolf-reel vintage look; no character dialogue/lip-sync | Images + simple clips from Meta AI extension are enough; no AI talking-character video needed |
| 2026-11-09 | Owner approved **test clips (~20–30 s) for both styles** in a separate `experiments/` folder before final architecture; legacy code untouched | Measure achievable quality before committing to a design |
| 2026-11-09 | Installed `ffmpeg` via Homebrew | Needed for frame/cut/loudness analysis and rendering |
| 2026-11-09 | Test toolchain: Python 3.12 venv (Kokoro, mlx-whisper), Node 22 + Remotion 4.0.537 pinned, in `experiments/` (see `experiments/README.md`) | Python 3.14 too new for ML libs; Node 26 hangs Remotion |
| 2026-11-09 | Caption words always come from the script; Whisper only supplies timing | Whisper misspells names ("Skulsy" → "Skulce") and mishears phrases |
| 2026-11-09 | Edit plan = JSON of shots anchored to **word indexes** (not seconds) + layers + entrance + SFX; Remotion renders it | Re-voicing doesn't break the plan; it's the contract between Claude and the renderer |
| 2026-11-09 | Final step normalizes loudness to −14 LUFS | First render was −21 LUFS (too quiet for social) |
| 2026-11-09 | Meta AI images generated by **Claude driving meta.ai directly via Claude in Chrome** (one chat, one prompt at a time, page-script download). The Meta Automation side panel can't be driven by Claude | Owner granted permission; ~30 s per image; works without the extension |
| 2026-11-09 | Story numbers come from real data and the script is corrected to match it (e.g. 2022 drop is 59% peak-to-trough, not "almost half"); images showing wrong numbers get covered by an overlay | Accuracy = value add + trust; Meta AI invents on-screen numbers |
| 2026-11-09 | **Renderer = Remotion only.** ffmpeg for finishing (loudness) and analysis. **No MoviePy, no HyperFrames** | MoviePy is slow and weak at motion graphics. HyperFrames (HeyGen, Apache-2.0) duplicates Remotion (both: code → headless Chrome → ffmpeg). Revisit HyperFrames only if the business grows past Remotion's free licence (≤3 people); plan.json would stay the same |
| 2026-11-09 | Meta extension safeguards: separate Meta account (not the Facebook page owner), keep delays on, test watermark/labels, check output commercial-use terms | Meta terms restrict automated access; protect the Facebook page account |
| 2026-11-09 | OpenChatCut `explainer-video` skill analysed, **not installed** (`docs/OPENCHATCUT_SKILL_ANALYSIS.md`). Proposal (**awaiting owner OK**): borrow its ideas (explanation test, claim → visual table, honest-chart rules, sync QA checklist, hardest-section-first) and write our own skills in our own words: shared `video-core` + one skill per style + a `check_plan.py` validator | It is 2 Markdown files, built for the OpenChatCut app (missing sibling skills/tools here); text is GPL-3.0, so copy ideas, not wording |
| 2026-11-09 | Ponytail (`DietrichGebert/ponytail`) analysed, **not installed** (`docs/PONYTAIL_SKILL_ANALYSIS.md`). It is a coding-minimalism skill, **not video editing**. Proposal (**awaiting owner OK**): skip the plugin (adds hooks to every session + stat logging); optionally add its "smallest complete change" rules to `CLAUDE.md` when engine building starts | Useful for keeping engine code small and understandable; irrelevant to video quality |
| 2026-11-09 | **Agreed:** write our own skills, one per niche/style (plus a shared core), instead of installing OpenChatCut's. A niche skill is refined over time: owner drops screenshots / reference videos / notes into `references/<niche>/`, Claude measures and analyses them and updates that niche's skill (each change logged here) | Owner can steer a niche with examples instead of rewriting rules; each niche stays independent |
| 2026-11-09 | **Agreed:** Ponytail plugin not installed; its useful rules adapted into a "Coding rules" section of root `CLAUDE.md` (loaded every session). Kept: skip-unasked-features ladder, reuse first, no new dependency without owner OK, finish all touched places, root-cause bug fixes, small tests for money/timing/parsing logic, `shortcut:` comments, never-cut list, end reply with skipped/risks. Dropped: hooks, stats logging, "ultra" push-back mode, shortest-diff-over-clarity | Keeps engine code small and readable for the owner without extra background scripts |
| 2026-11-09 | **Old research method replaced** (`docs/RESEARCH_REVIEW.md`). Numbers only from official data via tested scripts (Tiingo daily adjusted + Alpha Vantage adjusted cross-check, FRED, SEC EDGAR); events from 2 reputable sources; every script number in `facts.json`; owner gets `facts_review.md` to check manually. **Proposed, awaiting owner OK** | Old code: every stock looked up as SPY, unadjusted prices, rate-limit errors cached as data, LLM 'verifier' told not to check numbers |
| 2026-11-09 | Images: **Claude drives meta.ai via Claude in Chrome by default**; Meta extension kept as manual option | Owner's choice; extension option saves Pro usage when needed |
| 2026-11-09 | After the B1 cleanup, owner creates a GitHub repo and code is pushed there. `.gitignore` before first commit; `.env` files, legacy media, caches, venv, node_modules, renders never pushed; owner checks file list before first push | Owner's plan; protect API keys and stay under GitHub size limits |

## 7. Open questions (waiting on owner)

1. ~~Claude access~~ → resolved: Claude Code on personal Pro subscription.
2. ~~Length~~ → resolved: 2:00–2:48.
3. Reference: owner to supply wolf/pig channel videos in `YouTubeAutomation/reference_reels/` (created 2026-11-09; `YouTubeAutomation/` made owner-writable, it was read-only) + detailed edit/style breakdown with screenshots.
4. ~~Meta AI extension~~ → feasible (see decisions); final adoption after style is locked.
5. Skulsy character assets and sidekick design: deferred until format/style is decided.
6. Setup prerequisite: `ffmpeg` is not installed on the Mac yet.

## 8. Session log

- **2026-11-09, session 1:** Analyzed the legacy codebase; proposed general improvements (orchestrator, profiles, provider layer, quality gates, cleanup). Owner gave full requirements (sections 1–4). Drafted target architecture v0 (proposed, **not yet agreed**; see `docs/ARCHITECTURE.md` once written). Created this file and root `CLAUDE.md`.
- **2026-11-09, session 1 (cont.):** Analysed reference reels (`docs/REFERENCE_ANALYSIS.md`). Built Style B test: `experiments/out/styleB_v2.mp4` (17 s, 21 shots, SVG Skulsy rig, wobble/shake, SFX per cut, −14.7 LUFS). Style A prepared: real NVDA data script (`experiments/styleA_test/script.txt`), 12 Meta AI prompts (`meta_prompts.txt`). **Waiting on owner:** watch/listen to Style B; generate Style A images via Meta AI into `experiments/styleA_test/incoming/`.
- **2026-11-09, session 1 (cont. 2):** Claude generated all 12 Style A images on meta.ai via Claude in Chrome (one refused prompt replaced by Meta's own alternative). Built Style A test: `experiments/out/styleA_v2.mp4` (40 s, 20 shots, real NVDA chart with counter, year stamps, film grain/flicker/weave, serif captions, end card, −14 LUFS). **Waiting on owner:** watch/listen to both test videos and give feedback on voice, SFX, pacing, look; then decide which style(s) go forward and plan the real architecture.
- **2026-11-09, owner feedback:** Voices fine (try other Kokoro voices too); SFX fine; both styles good, both to be improved. Asked for a behind-the-scenes flow summary and Pro-plan capacity. Answer: only script, edit plan, review and Chrome image generation use Claude tokens; Chrome image generation is the most expensive step and should move off Claude (extension Start button or background script). Capacity to be **measured** on one production video via `/usage` (Anthropic doesn't publish exact Pro limits). Next: architecture plan.
- **2026-11-09, session 2:** Did HANDOFF next step 1: read the OpenChatCut `explainer-video` skill from GitHub as plain text (not installed). Report in `docs/OPENCHATCUT_SKILL_ANALYSIS.md`. **Waiting on owner:** agree to the recommendation (own skills, ideas borrowed), then step 2 = architecture plan.
- **2026-11-09, session 2 (cont.):** Owner asked to analyse the Ponytail skill (believed to be for video editing). Read from GitHub, not installed: it is a coding-style skill, not video. Notes in `docs/PONYTAIL_SKILL_ANALYSIS.md`. **Waiting on owner:** OK on both skill recommendations, then step 2 = architecture plan.
- **2026-11-09, session 2 (cont. 2):** Owner agreed: own per-niche skills (refined with owner's screenshots/details in `references/<niche>/`), and Ponytail rules kept in `CLAUDE.md`. Added the "Coding rules" section to `CLAUDE.md`. Next: step 2, architecture plan (includes skill layout + niche refinement workflow).
- **2026-11-09, session 2 (cont. 3):** Owner asked for the architecture (other open items wait until the codebase is refactored to it). Wrote `docs/ARCHITECTURE.md` v1 (**proposed, awaiting owner approval**): run folders, plan.json v1 + check_plan.py, skills = video-core + style-* + niche-*, niche refinement via `references/<niche>/`, Meta extension as default image source, cleanup (archive, nothing deleted), git init, build order B1–B5.
- **2026-11-09, session 2 (cont. 4):** Owner asked to verify the old research method. Found serious bugs (wrong ticker → SPY for all stocks, unadjusted prices, cached rate-limit errors, no number checking). Wrote `docs/RESEARCH_REVIEW.md` and updated `docs/ARCHITECTURE.md` to v1.1 (research §6a, Claude-in-Chrome images default + manual extension, GitHub push rules, step B1b). **Waiting on owner:** approve v1.1; Tiingo free key; contact name for SEC EDGAR requests.
