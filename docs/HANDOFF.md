# Session Handoff (end of session 2, 2026-11-10)

> **New chat? Read this file first.** It is the complete, compact state of the project up to now.
> Then, as needed: `docs/CONTEXT.md` (requirements, every decision, session log) · `docs/ARCHITECTURE.md` (how the engine works, change log) · `.claude/skills/video-core/SKILL.md` (how to make a video, exact commands) · `engine/README.md` (setup + tools).
> Rules (from `CLAUDE.md`): **plan → owner agrees → build**; log every decision in `docs/CONTEXT.md`; follow the "Coding rules" section in `CLAUDE.md`.

---

## 1. What we're building
A local, Claude-directed engine that makes **faceless vertical videos (2:00–2:48)** for **Facebook first, then YouTube**, uploaded **manually** by the owner.
- First niche: **Skulsy (friendly cartoon skeleton) + USA finance**. Later more niches, each as its own skill.
- Must be **monetizable**: real data, a story, motion graphics. Not an AI slideshow (that got the old channel demonetized).
- Free / open-source first. Runs on the owner's MacBook Pro (24 GB).
- Brain = **Claude Code on the owner's personal Pro plan** (never the office/enterprise account).
- Target later: ~3 videos/day.

## 2. Current state (everything built so far)
| Area | State |
|---|---|
| Architecture | **v1.2 approved and built** (steps B1–B5). `docs/ARCHITECTURE.md` |
| Engine tools | `engine/tools/`: new_run, fetch_data, finance_calc, voice, match_images, check_plan, render.sh, finish, contact_sheet, facts_review, make_sfx. **32 tests pass** (`engine/.venv/bin/python -m unittest discover -s engine/tests`) |
| Renderer | `engine/remotion/` (Remotion 4.0.537, Node 22). One composition per style; renders any run folder. **Working**: both tests rendered |
| Skills | `.claude/skills/`: `video-core`, `style-vintage-story`, `style-flat-fastcut`, `niche-skulsy-finance` |
| Library | `library/sfx/` (10 generated placeholder SFX) + `sfx.json`; `library/music.json` (empty: no licensed music yet) |
| Test videos | `runs/2026-11-09_test-vintage-nvda/out/final.mp4` (43 s, NVIDIA story, corrected numbers) and `runs/2026-11-09_test-flat-timing/out/final.mp4` (18 s, over-trading comedy). Both −14 LUFS, reviewed. Copy of vintage in `~/Downloads/skulsy_vintage_nvda_test.mp4` |
| Git | Local repo, branch `main`, **not pushed**. `.gitignore` excludes `.env`, media, caches, venvs, node_modules. Checked: no API keys in tracked files |
| Cleanup | Legacy `YouTubeAutomation/` and `experiments/` **removed** (owner's request) → in `~/.Trash/finance-agent-cleanup-2026-11-09/` until the owner empties it. Old code also restorable: `git show 3c768e1:YouTubeAutomation/<path>`. Project folder ≈ 2.8 GB |

## 3. Folder map
```
CLAUDE.md               project rules + coding rules (read every session)
.env                    API keys (never commit/print)
docs/                   HANDOFF (this), CONTEXT, ARCHITECTURE, RESEARCH_REVIEW, LEGACY_AUDIT,
                        REFERENCE_ANALYSIS, OPENCHATCUT_SKILL_ANALYSIS, PONYTAIL_SKILL_ANALYSIS
.claude/skills/         video-core, style-vintage-story, style-flat-fastcut, niche-skulsy-finance
engine/                 tools/, tests/, remotion/, requirements.txt, .venv/ (Python 3.12), cache/
library/                sfx/ + sfx.json, music/ + music.json, characters/, fonts/
references/             README.md (how owner refines a niche) + skulsy-finance/ reel1 + reel2
runs/<date>_<slug>/     one folder per video: brief, data, facts.json, script, voice, words, plan, img, review, out
archive/                old skills/patterns + root leftovers (credited by the new skills)
```

## 4. Key decisions (short; full list in `docs/CONTEXT.md` §6)
- **Renderer = Remotion only** (Node 22; Node 26 hangs it). ffmpeg for finishing. No MoviePy, no HyperFrames.
- **Skills:** one shared `video-core` + one skill per **style** (look) + one per **niche** (content). Owner refines a niche by dropping screenshots/reels/notes into `references/<niche>/` → Claude analyses → proposes skill changes → applies after OK.
- **OpenChatCut "explainer-video"** skill analysed, not installed; its ideas (explanation test, claim → visual table, honest charts, sync QA) rewritten in our own words (its text is GPL). **Ponytail** analysed (coding-minimalism, not video), not installed; its useful rules are the "Coding rules" in `CLAUDE.md`.
- **Research / numbers (finance: a wrong number is a real problem):** old research code was broken (every stock looked up as SPY, unadjusted prices, cached rate-limit errors). Now: `fetch_data.py` (Tiingo daily adjusted + Alpha Vantage cross-check, FRED, SEC EDGAR) → `finance_calc.py` (tested) → `facts.json`. **Every number in a script or on screen must be a facts.json `say` value** (years excepted), written as digits; `check_plan.py` refuses anything else. Story-only numbers = `"kind": "illustrative"`. Owner gets `review/facts_review.md` to tick before upload.
- **Images:** Claude drives meta.ai via Claude in Chrome by default; Meta extension = manual option. No numbers/text in prompts (Meta AI invents them); check the contact sheet and crop out any.
- **Voices:** Kokoro local. vintage = `bm_george` 0.95; flat = `am_puck` 1.1. Owner wants to audition more.
- **Video length 2:00–2:48**, −14 LUFS. Shot limits: vintage 0.5–7 s; flat 0.25–2.5 s (last ≤ 4 s); flat signs out of the caption band.
- **GitHub:** owner will create a repo (private recommended); Claude must show the file list before the first push.

## 5. Things a new session must know (traps)
- **Rendering must run outside Claude Code's sandbox** (headless Chrome can't reach Remotion's local server inside it). The owner has given permission. If refused, the owner types `! engine/tools/render.sh runs/<id>`.
- **zsh does not word-split `$VAR`**: `$P $T args` fails; write commands out in full or use `${=VAR}`. macOS has no `timeout` command.
- **No new Python packages without owner OK** (Pillow is not installed; contact-sheet labels go in `review/sheets.txt`).
- Alpha Vantage free tier ≈ 25 requests/day, and daily adjusted prices are paid there → use Tiingo (key missing) or `--source av-weekly --check none`.
- Owner couldn't hear audio when previewing a final video: the file is fine (verified by transcription); use QuickTime/VLC, not an editor preview pane.
- Kokoro: write "A I" not "AI", "262 times" not "262x". Whisper misspells "Skulsy" (harmless: captions come from the script).

## 6. Waiting on the owner
1. Watch both test videos and give feedback (look, voice, pacing, SFX).
2. Free **Tiingo** key → `TIINGO_API_KEY=` in `.env` (then re-fetch NVDA daily and re-check the Style A facts; weekly data may shift numbers slightly).
3. Contact for SEC data → `SEC_USER_AGENT="Name email"` in `.env`.
4. Create the **GitHub repo**; Claude lists files, owner confirms, then first push.
5. Empty the Trash when sure nothing is missing (frees 7 GB).

## 7. Next steps (after the owner's items)
1. First **production-length video (2:00–2:48)** end to end with `video-core`; measure Pro usage with `/usage`.
2. Refine styles from the owner's feedback / new references (`references/skulsy-finance/`).
3. Open items: licensed background music + real SFX (licences recorded in the json indexes), more Kokoro voice auditions, a Skulsy pose set for the vintage style, maybe image generation off Claude to save tokens.
