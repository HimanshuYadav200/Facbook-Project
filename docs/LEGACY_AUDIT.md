# Code audit during the rebuild (2026-11-09)

Owner's request: while building the engine, find and fix every wrong / weak / breaking piece in the earlier code, not only the research code.
Scope: everything carried forward into the engine (our `experiments/` test code, the legacy skills and patterns) plus a scan of the legacy `YouTubeAutomation/` modules for lessons. Legacy Python modules are **retired, not fixed**: the engine replaces them (see "Retired" below).

## A. Wrong numbers found in content

| Where | Problem | Fix |
|---|---|---|
| Style A test script | "Lost 59%" figure came from **monthly** closes; weekly data shows **66%** (peak 2021-11-19 → trough 2022-10-14) | script says "more than half" (true); fact recorded with dates |
| Style A test script | "A year later? $45,000": that was the Nov-2021 **peak month**, not one year later. End-2021 value is **$41,100** | corrected |
| Style A test script + sticker | "Today about $287,000" / "$287K": wrong; the video's own chart ended at ~$262k. Value on 2026-11-06 is **$262,000** | corrected (script + sticker) |
| Legacy "What if" pattern example | "Amazon at $5 in 2001 … $3,500 in 2021 … $7 million" mixes **unadjusted** share prices (Amazon split 20:1 in 2022) | patterns rewritten: talk in dollars invested; no example numbers |
| Legacy research cache | Amazon / Enron / Starbucks topics all got **SPY** prices; prices **unadjusted**; rate-limit errors cached as data | see `docs/RESEARCH_REVIEW.md`; replaced by `fetch_data.py` + `finance_calc.py` |

## B. Our test code (`experiments/`) → fixed in `engine/`

| # | Problem | Effect | Fix (file) |
|---|---|---|---|
| 1 | Kokoro language always American (`lang_code="a"`) | British voice `bm_george` mispronounced words | language from voice name (`engine/tools/voice.py`) |
| 2 | Vinyl / room-tone beds are 40 s files, played once | ambience would stop at 0:40 in a 2:30 video | beds loop (`common/AudioBed.tsx`), loop edges faded (`make_sfx.py`) |
| 3 | Chart hard-coded: "$1,000 IN NVIDIA", "January 2016", scale $500–$500k, years 2016–2026, colour rule `>= "2026"` | unusable for any other video | everything from plan `charts` + data file (`VintageChart.tsx`) |
| 4 | Chart with a mistyped month → `findIndex = -1` | silently drew garbage | dates resolved on-or-before; errors thrown; check_plan checks ranges |
| 5 | Chart source line one long line | ran off the frame | two lines |
| 6 | Loudness: single-pass `loudnorm` | volume can "pump" | two-pass linear (`finish.py`) + checks length / black frames / final LUFS |
| 7 | `finalize.sh` had no error handling or argument check | failures passed silently | `finish.py` exits non-zero with the reason |
| 8 | Word timings could run past the audio or go backwards (skipped words at the end) | captions / shots after the end | clamped and kept in order (`voice.py`) |
| 9 | No warning when the voice misreads the script | wrong pronunciations unnoticed | `voice.py` reports % of words heard as written, warns < 85% |
| 10 | Shot word index out of range → crash deep in Remotion | unclear error | clear error in `timing.ts`; caught earlier by check_plan |
| 11 | Plans/data/paths hard-coded per style in `Root.tsx` (`styleA/nvda.json`, `styleB/voice.wav`) | one video per style only | renders any run folder (`--public-dir`), style chosen by `plan.style` |
| 12 | Caption cleaning cut "U.S." to "U.S" | wrong caption | abbreviations kept (`Caption.tsx`) |
| 13 | Style B test: two shots shorter than ~8 frames ("Sold."/"Up." 0.16 s) | flash nobody can see | check_plan min length; shot merged |
| 14 | Style B test: signs and phone under the centred caption | text on text (seen on contact sheet) | check_plan warning + style rule; plan fixed |
| 15 | Copied Remotion project carried a stale webpack cache with old paths | possible odd bundles | cache cleared |
| 16 | Scripts spelled numbers ("forty five thousand") | captions show 3 words; numbers can't be checked | digits only, enforced by check_plan |

## C. Legacy skills and patterns → rewritten

| Legacy | Problem | Now |
|---|---|---|
| `script_patterns/*.md` (8 patterns) | all timed for 45 s; example numbers unverified/unadjusted; "fake precision" advice ("$47,329"); dialogue pattern needs multiple voices | `niche-skulsy-finance/references/script-patterns.md` for 2:00–2:48, facts-only numbers, single narrator |
| Two different `BASE_VIRAL_STRUCTURE.md` copies | which one is right? | merged into the shared shape in script-patterns.md |
| `humanizer/SKILL.md` | "be opinionated: ban 'it depends', write 'This proves…'" = overclaiming in finance | `writing-style.md` keeps the anti-AI-writing rules, drops overclaiming |
| `research_agent/SKILL.md` | good principles, code ignored them | principles in `video-core/references/data-honesty.md`, enforced by tools |
| `validators.py` banned-phrase list (8 phrases, never enforced on numbers) | | extended list enforced by check_plan |

## D. Retired legacy modules (not carried forward) and why

| Module | Main issues | Replaced by |
|---|---|---|
| `research_agent.py` | wrong ticker (SPY fallback), unadjusted prices, cached errors, silent fallbacks, fixed 1-year ROI, hard-coded "high confidence" | `fetch_data.py`, `finance_calc.py` |
| `verification_agent.py` | LLM told not to check numbers; on failure returns the unchecked script | `check_plan.py`, `facts_review.py` |
| `script_agent.py` | "number locking" only checked numbers survived rewrites, not that they were true | facts.json rule |
| `editor_agent.py` (MoviePy, 992 lines) | falls back to **estimated** word timings when Whisper fails (captions drift silently); MoviePy slow, weak motion graphics | Remotion + voice.py (no estimation: fails loudly) |
| `timing_utils.estimate_word_timings` | fake timing presented as real | removed |
| `audio_agent.py` | ElevenLabs/Google paid TTS with key switching | Kokoro local (`voice.py`) |
| `sfx_agent.py`, `visual_agent.py`, `image_gen_agent.py` | Gemini-driven, hard-coded providers, manual Grok/Whisk steps | style skills + library + match_images.py |
| `main.py` (1,367 lines) | monolith, `input()` prompts, folder polling | small one-job tools + video-core skill |
| Root `debug_*.py`, `test_*.py`, `temp_skulsy_code.py`, `validation_output*.txt` | Windows paths, scratch files | `archive/root_leftovers_2026-02/` |

## E. Still open
- Rendering inside Claude Code's sandbox hangs (headless Chrome can't reach Remotion's local server); renders must run outside the sandbox (owner runs `! engine/tools/render.sh …` or allows it). The new renderer type-checks but **has not rendered yet**.
- Prices are weekly (Alpha Vantage) until a Tiingo key is added; daily data may move numbers slightly.
- Placeholder SFX are generated; real licensed SFX/music still open.
