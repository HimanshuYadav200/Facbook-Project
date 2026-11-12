# Session Handoff (end of session 4, 2026-11-12)

> **New chat? Read this file first.** It is the complete, compact state of the project.
> Then, as needed: `docs/CONTEXT.md` (requirements, every decision, session log) · `docs/ARCHITECTURE.md` (how the engine works, change log, now v1.9) · `.claude/skills/video-core/SKILL.md` (how to make a video, exact commands) · `engine/README.md` (setup + tools).
> Rules (from `CLAUDE.md`): **plan → owner agrees → build**; log every decision in `docs/CONTEXT.md`; follow the "Coding rules" in `CLAUDE.md`. Commit only when the owner asks.

---

## 1. What we're building
A local, Claude-directed engine that makes **faceless vertical short videos** for **Facebook and YouTube**, uploaded **manually** by the owner, aimed at a **US audience**. One skill per **niche** (content) and per **style** (look); Claude drives every step. Free / open-source first, runs on the owner's MacBook Pro (M5, 24 GB). Brain = Claude Code on the owner's Pro plan. Owner's plan: ~60 reels per niche on 3 Facebook Pages, scheduled over a month (3–4 a day per Page, at different US times).

## 2. Niches
| Niche | Style | Length | Status | Videos made (all in `runs/<niche>/`, copies in `~/Downloads/`) |
|---|---|---|---|---|
| **strange-money**: true strange money stories, scams, loopholes | `explainer-fast` | 45–70 s | **Ready, producing.** Facebook Page being set up (name/bio/categories in the niche skill; cover + profile in `library/brand/strange-money/` and `~/Downloads/strange_money_fb_*.png`) | 6: eiffel-tower-sale, lustig-cons-capone, ford-van-seats, hanoi-rat-bounty, parmesan-bank, **lucas-toy-rights** (newest, made with all session-4 fixes: slower voice, new SFX, auto fact check) |
| **stickman-money**: calm stickman parables, one money lesson | `stickman-calm` | ~1:30 | **Ready.** Page art in `library/brand/stickman-money/` | 4: two-brothers-paycheck, earn-ten-dollars, same-raise, parents-said-no |
| **skulsy-finance**: Skulsy skeleton + real USA finance data | `vintage-story` / `flat-fastcut` | 2:00–2:48 | **Not ready** (two short tests only) | needs a full video, owner feedback, `TIINGO_API_KEY` + `SEC_USER_AGENT` in `.env` |

Next strange-money topics (first-week order in `niche-strange-money/references/topics.md`): **#32 Poyais**, #4 Pepsi Harrier jet, #70 Hoover free flights, #5 Yap stone money … (#31, #50, #2, #92, #105 used).

## 3. Engine state (69 tests pass: `engine/.venv/bin/python -m unittest discover -s engine/tests`)
| Area | State |
|---|---|
| Tools | `engine/tools/`: new_run, fetch_data, finance_calc, voice, **meta_save.js**, match_images, key_green, find_eyes, check_plan, render.sh, finish, contact_sheet, **fact_check**, facts_review, make_sfx, **gen_sfx**. Table: `engine/README.md` |
| Fact checking | `fact_check.py`: Tavily + Exa per fact (facts carry `search` + `key`), `review/fact_check.md`, `--apply` clears manual marks. Keys in `.env`: `TAVILY_API_KEY`, `TAVILY_API_KEY_BACKUP` (2 × 1,000 free/month), `EXA_API_KEY` ($10 free/month ≈ 1,400 searches). Run it **before** recording the voice. |
| Voice | strange-money default: **`am_puck` 1.05 + `--sentence-gap 0.2`** (~185 wpm; owner confirmed 2026-11-12). Samples: `~/Downloads/voice_samples_strange_money/` |
| SFX | 147 sounds in `library/sfx/` (Mixkit + freesound CC0 + 5 generated `gen_*`). explainer-fast mix: whoosh every other cut, quieter (cut 0.14 / mg 0.25 / sfx 0.22), realistic pools in `sounds.json`. Local model **Stable Audio 3 Small SFX** in `~/tools/stable-audio-3` (`gen_sfx.py`, runs inside the sandbox, offline). **Mixkit files never shared alone, no Content ID; `*.wav` git-ignored.** |
| Checks | check_plan: numbers vs facts.json (`$365 million` allowed; counters read number + word), graphics ≥ 1 s. finish: −14 LUFS, length, **true peak ≤ −1 dB**, black frames |
| Images | Meta AI via Claude in Chrome + `meta_save.js` (one prompt at a time; saves the **last** image on the page, refuses byte-identical repeats; 2 images per browser batch). ~32 images ≈ 25–30 min per video |
| Blinks | find_eyes handles hair over the head + round glasses (the 4 old stickman videos still have old `eyes.json`; re-render only if the owner asks) |
| Git | Remote `origin` = github.com/HimanshuYadav200/Facbook-Project; **both branches pushed 2026-11-12** (`main` + `session-3-niches`, tracking set). All session 3–4 work is on `session-3-niches`; `main` on GitHub is still the older state → merge when the owner wants (PR link: github.com/HimanshuYadav200/Facbook-Project/pull/new/session-3-niches). Pushing from Claude was blocked by auto mode: the owner runs `! git push` |

## 4. Waiting on the owner
1. ~~Push to GitHub~~: done 2026-11-12. Later: merge `session-3-niches` into `main`, then `! git push`.
2. ~~Stability AI licence~~: **activated 2026-11-12** → `gen_*` sounds may be used in uploads.
3. ~~Voice default~~: confirmed am_puck 1.05 + gap 0.2 (in the niche skill).
4. Watch + upload: Lucas video (`~/Downloads/strange_money_lucas_toy_rights.mp4`, `upload.md` says 12:30 PM Eastern) and the others; stickman videos still need their illustrative facts ticked.
5. Eiffel video peaks at +0.1 dB (clips slightly): re-finish/re-render only if the owner wants.
6. Optional: Sonniss GDC 2026 SFX zips (5 links in CONTEXT session 4 cont. 4) downloaded by hand → Claude picks sounds.
7. skulsy-finance: Tiingo key + SEC contact; feedback on the tests.

## 5. Next steps
1. Produce more strange-money videos from the first-week order (video-core + niche + style skills). Facts → `fact_check.py --all` → script → voice → plan → images → check → render → finish → review → upload.md.
2. Stickman-money videos for the owner's 60-per-niche plan (seed bank: `niche-stickman-money/references/topics.md`, 4 of 100 used).
3. Later scope: multi-angle AI animation, Blender R&D, blinks on explainer actors, more voices, skulsy-finance.

## 6. Traps (read before working)
- **Render outside the sandbox** (`render.sh` with sandbox disabled; owner allowed it). Take `runs/<niche>/.render.lock` (mkdir) when agents run in parallel.
- **Heat:** 4 parallel meta.ai tabs + renders overheated the Mac → one browser tab at a time.
- **Browser tool limits:** one JS call stops after 45 s (`metaSave.wait(38000)`, call twice); a browser batch with 4 image prompts times out → 2 per batch.
- **Meta AI:** reloads old images under new addresses as the chat grows (meta_save.js handles it); refuses look-alikes of protected characters (e.g. "furry plush creature" = Chewbacca); sometimes drifts to realistic people (say "NOT realistic people"); adds the main character to scenes uninvited; invents text → check the contact sheet.
- Labels are upper-cased: "1970s" shows as "1970S".
- **zsh doesn't word-split `$VAR`**; no `timeout` on macOS; ffmpeg has **no drawtext**; PIL/librosa not installed (no new packages without owner OK).
- Never overwrite renders/plans: back up as `out/v1_final.mp4`, `plan_v1.json` first.
- Kokoro: "A I" not "AI"; amounts as digits (`$365 million`, never `$365M`); every on-screen number must be in `facts.json`.
- `.env` keys are never printed or committed. Owner previews: QuickTime/VLC (some players are silent).

## 7. Folder map
```
CLAUDE.md               project rules + coding rules
.env                    API keys (never commit/print)
docs/                   HANDOFF (this), CONTEXT, ARCHITECTURE, analyses
.claude/skills/         video-core (+ references/upload-policy.md, data-honesty.md), style-*, niche-*
engine/                 tools/, tests/, remotion/, .venv/ (Python 3.12)
library/                sfx/ + sfx.json, music/, brand/<niche>/ (Page art)
references/             per-niche reference reels + analysis.md
runs/<niche>/<date>_<slug>/   one folder per video: brief, script, facts.json, voice, words, plan, img, review, out, upload.md, log.md
~/tools/stable-audio-3  local SFX model (separate venv, outside the project)
```
