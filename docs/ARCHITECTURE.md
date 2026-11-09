# Architecture: faceless video engine

> Status: **v1.2 APPROVED (2026-11-09) and BUILT (B1–B5)**, except the first render through the new renderer (blocked by the sandbox, see §13). Audit of old code: `docs/LEGACY_AUDIT.md`.
> Read with `docs/CONTEXT.md` (requirements and decisions). This file explains *how the engine works*, *where each part lives*, and *how to fix it*. The change log is at the bottom.

---

## 1. The idea in one paragraph

Claude Code (owner's Pro plan) is the **director**: it researches, writes the script, writes the edit plan and reviews the result. Everything heavy runs as **local tools that cost no tokens**: Kokoro makes the voice, Whisper times every word, Remotion draws and renders the video, ffmpeg finishes the audio. The bridge between the director and the renderer is one file, **`plan.json`**: a list of shots tied to *word positions* in the narration. How a video should look and sound is written down in **skills**: one shared core skill plus one skill per style and per niche. Every video lives in its own **run folder**, so it can be re-rendered or fixed at any time.

## 2. Flow of one video

`🧠` = Claude (uses Pro tokens). `⚙` = local tool (free). `👤` = owner.

```
👤 topic / niche
   │
1. 🧠 Brief + research        → runs/<id>/brief.md, data/*.json, facts.json
   │   ⚙ fetch_data.py (Tiingo, Alpha Vantage, FRED, SEC EDGAR; cached)
   │   ⚙ finance_calc.py (returns, drops, inflation; tested)   (§6a)
2. 🧠 Script                  → script.txt          (niche skill: patterns, tone, length)
3. ⚙ voice.py                 → voice.wav, words.json   (Kokoro + Whisper timings)
4. 🧠 Edit plan               → plan.json, image_prompts.txt   (style skill: look, pacing, SFX)
5. Art
   ├─ code-drawn style  → nothing to fetch (SVG characters/props in Remotion)
   └─ image style       → 🧠 Claude makes images on meta.ai via Claude in Chrome (default)
                           or 👤 manual: press Start in Meta extension (§8)
                           ⚙ match_images.py → img/   (rename by shot, remove duplicates)
6. ⚙ check_plan.py            → stops here if anything is wrong (§6)
7. ⚙ render.sh                → out/raw.mp4   (Remotion, Node 22)
8. ⚙ finish.py                → out/final.mp4 (−14 LUFS two-pass, length + black-frame checks)
9. ⚙ contact_sheet.py         → review/sheet_N.jpg  (one frame per shot + caption)
   🧠 Review against checklist → fix plan → back to 6   (max 2 rounds)
10. 🧠 upload.md              → title, description, hashtags
   │
👤 watch + upload manually (Facebook, then YouTube)
```

Why this order:
- **Voice before plan.** Shots are anchored to word timings, so the plan is written against the real audio (rule borrowed from OpenChatCut: never time visuals from estimates).
- **Checks before render.** Rendering takes minutes; a script catches broken plans in a second and costs no tokens.
- **One contact-sheet image per review round.** Reviewing images is the most token-expensive thing Claude does.

## 3. Folder layout

```
Finance-Agent(short-form)/
├─ CLAUDE.md                  project rules + coding rules (read every session)
├─ .env                       API keys (never committed, never printed)
├─ docs/                      HANDOFF, CONTEXT, ARCHITECTURE, analyses
├─ .claude/skills/            how videos are made (§4). Claude Code loads these
│   ├─ video-core/
│   ├─ style-vintage-story/   (today's Style A)
│   ├─ style-flat-fastcut/    (today's Style B)
│   └─ niche-skulsy-finance/
├─ engine/                    the code
│   ├─ tools/                 small Python/shell scripts, one job each (§5)
│   ├─ remotion/              renderer: common/ parts + styles/<style>/
│   ├─ requirements.txt       Python packages (pinned)
│   └─ .venv/                 Python 3.12 (not committed)
├─ library/                   reusable assets, shared by all videos
│   ├─ sfx/  + sfx.json       sound effects with tags + licence
│   ├─ music/ + music.json    background tracks with mood + licence
│   ├─ characters/skulsy/     owned character art (SVG rig, pose images)
│   └─ fonts/
├─ references/<niche>/        owner's screenshots, reels, notes → analysis.md
├─ runs/<date>_<slug>/        one folder per video (§7)
└─ archive/                   old files kept for reference, not used by the engine
```

`YouTubeAutomation/` (legacy, 4.4 GB) stays where it is, **untouched**. `experiments/` is retired once the engine re-makes both test videos (§11).

## 4. Skills: how styles and niches are written down

Two kinds of skill, because *what a video is about* and *how it looks* change independently (the vintage look could later serve a history niche; Skulsy could later use a new look).

| Skill | Answers | Contains |
|---|---|---|
| `video-core` | How is any video made here? | Pipeline steps + exact commands, `plan.json` rules, explanation rules, data honesty, review checklist, known errors |
| `style-*` | How does it **look and sound**? | Measured numbers from reference reels (shot length, caption size/font, colours, motion, SFX density), allowed shot types and their fields, image-prompt template, one known-good example plan |
| `niche-*` | What is it **about**, and for whom? | Audience, topic list/ideas, script patterns and hooks, tone, voice + speed, characters, data sources, default style, banned claims |

Each skill is a short `SKILL.md` (always read) plus a `references/` folder (read only when needed, to save tokens).

**video-core contents**
```
video-core/
  SKILL.md                 steps 1–10 above, commands, what to check at each step
  references/
    plan-schema.md         every plan.json field with examples
    explain-rules.md       explanation test + finance claim → visual table
    data-honesty.md        sources, adjusted prices, every number traceable
    review-checklist.md    what to look for on the contact sheet + sync checks
    known-errors.md        Node 22, Whisper misspellings, Meta AI quirks, …
```

**Explanation rules** (ideas from OpenChatCut, written in our own words): style motion (wobble, shake, fast cuts) is allowed everywhere, but every **teaching beat** must pass the test *"the viewer understands ___ because the screen shows ___ changing."* Finance mapping:

| Claim in script | Visual |
|---|---|
| Price/value over time | Line chart drawing in + $ counter |
| A crash / drop | Peak-to-trough marker with % |
| A vs B | Bars or lines on one shared axis |
| Compounding / growth | Growing stack or counter, with years |
| Cost of a habit | Counter adding up per day/month/year |

**Refining a niche or style (owner's workflow)**
1. Owner drops screenshots / reels / notes into `references/<niche>/` (e.g. "captions should look like this", "cuts faster here").
2. Claude measures them (ffmpeg: cut timing, frames, colours) and writes `references/<niche>/analysis.md`.
3. Claude proposes the exact changes to the style or niche skill (and Remotion code if a new visual is needed); owner agrees; Claude applies them.
4. Change logged in `docs/CONTEXT.md`. Next video uses the new rules automatically.

**New niche** = new `niche-*` skill (+ a new `style-*` skill and Remotion style folder only if the look is new). Core and tools stay the same.

## 5. Engine tools (each one small, one job, runnable by hand)

| Tool | In → Out | Notes |
|---|---|---|
| `new_run.py <slug>` | → `runs/<date>_<slug>/` with empty files | So every run has the same shape |
| `fetch_data.py` | exact ticker/series + dates → `data/<name>.json` | Tiingo daily adjusted + Alpha Vantage adjusted (cross-check), FRED, SEC EDGAR. Errors/rate limits never cached (§6a) |
| `finance_calc.py` | data → numbers for `facts.json` | $X invested, return %, CAGR, peak-to-trough, inflation-adjusted. Has tests |
| `voice.py` | `script.txt` → `voice.wav`, `words.json` | Today's `voice_and_timing.py`. Voice + speed come from the niche skill. Caption words from script, timing from Whisper |
| `voices.py` | → `library/voice_samples/*.wav` | Audition many Kokoro voices with one sentence (open item) |
| `match_images.py` | `incoming/` → `img/shot_XX.png` | Order by time, drop duplicates (md5), report missing |
| `check_plan.py` | run folder → OK or a list of errors | §6 |
| `render.sh` | run folder → `out/raw.mp4` | Node 22; stages plan/words/voice/data/img + library SFX/music as APFS clones in `engine/remotion/.stage/` and passes it as `--public-dir` (keeps big out/ files out of the bundle) |
| `finish.py` | `raw.mp4` → `final.mp4` | −14 LUFS (two-pass); fails if length outside 2:00–2:48, black frames, or loudness off |
| `facts_review.py` | `facts.json` → `review/facts_review.md` | owner's manual check table |
| `contact_sheet.py` | `final.mp4` + plan → `review/sheet_N.jpg` + `sheets.txt` | One frame per shot, 40 per sheet; labels in sheets.txt (this ffmpeg can't draw text) |
| `make_sfx.py` | → placeholder SFX | Kept until a real SFX library exists |

Remotion: one project in `engine/remotion/`. `common/` holds shared parts (captions, timing, charts, counters, SFX track, film grain, end card). `styles/<style>/` holds what is unique to a style. Each style registers one composition that reads the run folder via Remotion's `--public-dir` (verified: the flag exists in 4.0.537).

## 6. `plan.json` and automatic checks

Same idea as the tests (it worked): shots start at a **word index**, so re-voicing doesn't break the plan.

Shared fields (every style):
```json
{
  "version": 1,
  "style": "vintage-story",
  "voice": { "id": "bm_george", "speed": 0.95 },
  "music": { "track": "calm_piano_01", "volume": 0.12 },
  "captions": { "mode": "one-word" },
  "endCard": { "text": "SKULSY", "seconds": 2 },
  "shots": [
    { "from": 0, "type": "image", "sfx": "thud", "...style fields": "..." },
    { "from": 42, "type": "chart", "data": "nvda", "to": "2022-10",
      "teach": "viewer sees the 59% drop as the line falls from peak to trough" }
  ]
}
```
Style-specific shot fields (motion, grade, layers, rig poses, …) are listed in that style's skill.

`check_plan.py` refuses to render when:
- the plan has a field the style doesn't know, or a missing required field;
- a word index is out of range or shots are out of order;
- a shot is shorter/longer than the style allows (e.g. flat-fastcut ~0.5–1.5 s);
- an image, SFX or music file it names doesn't exist;
- a chart/teaching shot has no `teach` sentence (explanation test, written down);
- **a number in `script.txt` is not in `facts.json`** (every $ / % / year must have a source);
- total length will fall outside 2:00–2:48.

`facts.json` = every number the script uses: value, unit, date, source URL/API, how it was computed (e.g. "peak 2021-11-29 → trough 2022-10-14, adjusted close").

## 6a. Research and fact checking (finance: a wrong number is a real problem)

Full reasoning and the bugs found in the old method: `docs/RESEARCH_REVIEW.md`.

- **Numbers are never written by Claude or copied from search snippets.** Claude picks *what* to look up (exact ticker, exact dates); `fetch_data.py` gets it from official data and `finance_calc.py` computes it.
- **Sources:** prices = Tiingo daily adjusted, cross-checked with Alpha Vantage adjusted (>1% difference = stop); economy = FRED; company figures = SEC EDGAR; events/quotes = Claude web search on primary or top-tier sources, 2 independent sources each.
- **Delisted companies / anything without an API** → marked `manual check`.
- Raw replies kept in the run's `data/` so every number can be re-checked later.
- **Owner's manual check:** `review/facts_review.md` lists every claim, number and source link (manual-check items first) before upload.

## 7. A run folder

```
runs/2026-11-12_nvda-1000/
  brief.md          topic, angle, niche, style, target length
  facts.json        every number + its source
  data/             raw data (nvda.json …)
  script.txt
  voice.wav  words.json
  plan.json
  image_prompts.txt incoming/  img/
  review/           contact sheets + Claude's notes per round
  out/raw.mp4  out/final.mp4
  upload.md         title, description, hashtags, "not financial advice" line
  log.md            what was done, which skill versions, Pro usage if measured
```
To fix a published video later: edit `plan.json` (or `script.txt` → re-run `voice.py`), then re-run check → render → finish.

## 8. Images and characters

Characters are **owned assets** in `library/characters/` (SVG rig for flat style; a fixed pose set for image styles), never regenerated per video, so they stay consistent and original.

Scene images, by cost:

| Source | Claude tokens | Owner effort | Use |
|---|---|---|---|
| Code-drawn (SVG in Remotion) | none | none | flat-fastcut style |
| **Claude drives meta.ai in Chrome** (default, owner's choice) | **high** | none | image styles |
| Meta Automation extension (manual option) | none | press Start, files land in `incoming/` | when Pro usage is tight |
| Google Imagen via API (GCP credits) | none | none | later, when credits are set up |

Claude writes `image_prompts.txt` either way, so switching source is just a choice per video; `match_images.py` maps files to shots. Meta AI invents on-screen numbers → any image with text gets checked on the contact sheet and covered by an overlay if wrong.

## 9. Voice, SFX, music

- **Voice:** Kokoro (local, free). Voice + speed fixed per niche in the niche skill. ElevenLabs keys exist in `.env` but are paid: not used unless the owner decides.
- **SFX:** `library/sfx/` + `sfx.json` (`name, tags, mood, length, licence, source`). The plan names an SFX; style skill says how often (e.g. every cut for flat-fastcut). Starts with today's generated placeholders; real library is an open item (CC0 / free-licence sources, licence recorded per file).
- **Music:** `library/music/` + `music.json`, same idea, ducked under the voice. Must be licensed for Facebook + YouTube monetization (open item).
- **Loudness:** final mix −14 LUFS.

## 10. Token budget on the Pro plan

| Step | Claude? | Size |
|---|---|---|
| Research + facts | yes | medium (web/API reads) |
| Script | yes | small |
| Plan | yes | medium (≈ 80–120 shots for 2:30) |
| Images | yes by default (Claude in Chrome); none with manual extension option | **largest** |
| Render, finish, checks | no | none |
| Review | yes | 1 image per round, max 2 rounds |
| Upload text | yes | small |

Real usage per video is measured with `/usage` on the first production video (build step 3).

## 11. Cleanup of the current folder

| Item | Action |
|---|---|
| `YouTubeAutomation/` | untouched |
| Root leftovers: `debug_audio.py`, `debug_env.py`, `temp_skulsy_code.py`, `test_pattern_gen.py`, `test_validation_fix.py`, `validation_output*.txt`, `research_cache.db` | move to `archive/root_leftovers_2026-02/` (nothing deleted) |
| `.agent/skills/` (script patterns, humanizer, research agent) | useful parts rewritten into `niche-skulsy-finance` + `video-core`; originals moved to `archive/` |
| `.agents/skills/` (Tavily search/crawl) | move to `archive/` (Claude Code has its own web search) |
| `experiments/` | code moves into `engine/`; Python venv re-created from `requirements.txt` (venvs break when moved). Folder deleted **only after** the engine re-makes both test videos and the owner says OK |

**Version control + GitHub:** `git init` in B1 with a `.gitignore` written **before the first commit**. After cleanup the owner creates a GitHub repo and we push. Never pushed:
- `.env` and `YouTubeAutomation/.env` (API keys; checked: keys exist only in these two files);
- `YouTubeAutomation/` media (`output/` 2.4 GB, `assets/` 1.9 GB, temp mp4s) and all `*.db` caches;
- `.venv/`, `node_modules/`, `runs/*/out/`, rendered/downloaded media (GitHub blocks files > 100 MB).
Before the first push, Claude lists exactly what will be uploaded for the owner to confirm. Recommend a **private** repo.

## 12. Build order (after approval)

| Step | What | Done when |
|---|---|---|
| B1 | git init + `.gitignore`, folder skeleton, cleanup moves | layout matches §3, nothing deleted; owner then creates GitHub repo, first push after owner checks the file list |
| B1b | `fetch_data.py` + `finance_calc.py` with tests (§6a) | known cases pass; NVDA 2022 drop re-verified on daily data |
| B2 | Move code to `engine/`, render from a run folder | both test videos re-made from `runs/` and look the same |
| B3 | `check_plan.py`, `facts.json` check, `contact_sheet.py`, checks in `finish.sh` | broken plans are caught with a clear message |
| B4 | Skills: `video-core`, `style-vintage-story`, `style-flat-fastcut`, `niche-skulsy-finance` | a new short test video made only by following the skills |
| B5 | `library/` with `sfx.json`; `match_images.py` for the extension flow | plan picks SFX by name; extension files map to shots |
| → | HANDOFF step 3: first full 2:00–2:48 video + measure `/usage` | |

Later (not in v1): real SFX/music library, voice auditions, Skulsy pose set, Blender scenes, more niches.

## 13. If something breaks, look here

| Symptom | Where |
|---|---|
| Render hangs "Waiting for root component" | (a) Node 26 in use → `render.sh` uses Node 22; (b) Claude Code sandbox blocks headless Chrome ↔ local server → run the render outside the sandbox (`! engine/tools/render.sh runs/<id>`) |
| check_plan: number not in facts | fetch + `finance_calc.py`, add the fact; or fix the script |
| Caption covers a sign (flat) | move the sign out of y 760–930 (check_plan warns) |
| Caption word wrong | `script.txt` (captions come from it), then `voice.py` |
| Shot starts at wrong moment | `from` word index in `plan.json`; check `words.json` |
| check_plan says number missing | add it with its source to `facts.json`, or fix the script |
| Missing image | `match_images.py` report; `incoming/` |
| Too quiet / too loud | `finish.sh` |
| Look of a style wrong | that style's skill + `engine/remotion/styles/<style>/` |

## 14. Change log

| Date | Change | Why |
|---|---|---|
| 2026-11-09 | v1 proposed | Turn the approved style tests into a repeatable engine; owner asked for per-niche skills refined with screenshots |
| 2026-11-09 | v1.1: new research approach (§6a), Claude in Chrome = default image source with extension as manual option, GitHub push rules (§11), build step B1b | Old research code produced wrong numbers (wrong ticker, unadjusted prices, cached errors); owner's choice on images; owner will push to GitHub after cleanup |
| 2026-11-09 | v1.2 built: B1 (git, layout, archive), B1b (fetch_data, finance_calc + tests), B2 (engine/remotion renders any run; both tests converted with corrected numbers), B3 (check_plan, finish.py two-pass, contact_sheet, facts_review), B4 (skills video-core, style-vintage-story, style-flat-fastcut, niche-skulsy-finance), B5 (library/sfx + sfx.json, match_images). 16 issues fixed in our test code (`docs/LEGACY_AUDIT.md`) | Owner approved the plan and asked to fix every weak piece found on the way |
