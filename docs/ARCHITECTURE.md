# Architecture: faceless video engine

> Status: **v1.3 (2026-11-10)**: v1.2 built (B1–B5) + niches isolated (N1, §4a). Plan N2–N6 for the stickman-money niche approved, in progress (§12). Audit of old code: `docs/LEGACY_AUDIT.md`.
> Read with `docs/CONTEXT.md` (requirements and decisions). This file explains *how the engine works*, *where each part lives*, and *how to fix it*. The change log is at the bottom.

---

## 1. The idea in one paragraph

Claude Code (owner's Pro plan) is the **director**: it researches, writes the script, writes the edit plan and reviews the result. Everything heavy runs as **local tools that cost no tokens**: Kokoro makes the voice, Whisper times every word, Remotion draws and renders the video, ffmpeg finishes the audio. The bridge between the director and the renderer is one file, **`plan.json`**: a list of shots tied to *word positions* in the narration. How a video should look and sound is written down in **skills**: one shared core skill plus one skill per style and per niche. Every video lives in its own **run folder**, so it can be re-rendered or fixed at any time.

## 2. Flow of one video

`🧠` = Claude (uses Pro tokens). `⚙` = local tool (free). `👤` = owner.

```
👤 topic / niche
   │
1. 🧠 Brief + research        → runs/<niche>/<id>/brief.md, data/*.json, facts.json
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
│   ├─ niche-skulsy-finance/  SKILL.md + niche.json (machine rules: length, styles, banned)
│   ├─ niche-stickman-money/
│   └─ style-stickman-calm/
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
├─ runs/<niche>/<date>_<slug>/  one folder per video, grouped by niche (§7)
└─ archive/                   old files kept for reference, not used by the engine
```

Removed in the 2026-11-09 cleanup (owner's request): `YouTubeAutomation/` (legacy code + 4.3 GB media) and `experiments/` (replaced by `engine/`). Both are in the macOS Trash until emptied; legacy code is also in git history (commit `3c768e1`).

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

**New niche** = new `niche-*` skill with its `niche.json` (+ a new `style-*` skill and Remotion style folder only if the look is new). Core and tools stay the same.

## 4a. Niche isolation

Several niches run side by side (Skulsy finance, stickman money, later stickman relationships…). They must never share rules by accident.

| Separate per niche | Shared by all niches |
|---|---|
| `.claude/skills/niche-<n>/` (SKILL.md, topic bank, `niche.json`) | engine tools, Remotion styles (a look can serve many niches) |
| `references/<n>/`, `library/characters/<n or cast>/` | `library/sfx/`, `library/music/` |
| `runs/<n>/<date>_<slug>/` | `video-core` skill |

**`niche.json`** holds the rules the tools enforce: `length_seconds` [min, max], `styles` (first = default), `banned` phrases. `new_run.py --niche <n>` (required) copies it into the run; `check_plan.py` and `finish.py` read the run's copy (shared `load_niche()` in check_plan.py). Why a copy: editing a niche later never changes or breaks old runs. Voice + speed stay in the niche SKILL.md, because Claude picks them, not a tool.

## 5. Engine tools (each one small, one job, runnable by hand)

| Tool | In → Out | Notes |
|---|---|---|
| `new_run.py <slug> --niche <n>` | → `runs/<n>/<date>_<slug>/` with empty files + `niche.json` copy | So every run has the same shape and its niche's rules |
| `fetch_data.py` | exact ticker/series + dates → `data/<name>.json` | Tiingo daily adjusted + Alpha Vantage adjusted (cross-check), FRED, SEC EDGAR. Errors/rate limits never cached (§6a) |
| `finance_calc.py` | data → numbers for `facts.json` | $X invested, return %, CAGR, peak-to-trough, inflation-adjusted. Has tests |
| `voice.py` | `script.txt` → `voice.wav`, `words.json` | Today's `voice_and_timing.py`. Voice + speed come from the niche skill. Caption words from script, timing from Whisper |
| `voices.py` | → `library/voice_samples/*.wav` | Audition many Kokoro voices with one sentence (open item) |
| `match_images.py` | `incoming/` → `img/shot_XX.png` | Order by time, drop duplicates (md5), report missing |
| `check_plan.py` | run folder → OK or a list of errors | §6 |
| `render.sh` | run folder → `out/raw.mp4` | Node 22; stages plan/words/voice/data/img + library SFX/music as APFS clones in `engine/remotion/.stage/` and passes it as `--public-dir` (keeps big out/ files out of the bundle) |
| `finish.py` | `raw.mp4` → `final.mp4` | −14 LUFS (two-pass); fails if length outside the run's `niche.json` limits, black frames, or loudness off |
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
- total length will fall outside the run's `niche.json` limits.

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
runs/skulsy-finance/2026-11-12_nvda-1000/
  niche.json        copy of the niche's rules at creation time
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
| `YouTubeAutomation/` | **removed 2026-11-09** (owner): code in git history `3c768e1`; old videos/assets/temp files to Trash |
| Root leftovers: `debug_audio.py`, `debug_env.py`, `temp_skulsy_code.py`, `test_pattern_gen.py`, `test_validation_fix.py`, `validation_output*.txt`, `research_cache.db` | move to `archive/root_leftovers_2026-02/` (nothing deleted) |
| `.agent/skills/` (script patterns, humanizer, research agent) | useful parts rewritten into `niche-skulsy-finance` + `video-core`; originals moved to `archive/` |
| `.agents/skills/` (Tavily search/crawl) | move to `archive/` (Claude Code has its own web search) |
| `experiments/` | code moved into `engine/`; folder **removed 2026-11-09** (owner) after both tests re-rendered with the engine |

**Version control + GitHub:** `git init` in B1 with a `.gitignore` written **before the first commit**. After cleanup the owner creates a GitHub repo and we push. Never pushed:
- `.env` (API keys);
- all `*.db` caches;
- `.venv/`, `node_modules/`, `runs/*/*/out/`, rendered/downloaded media (GitHub blocks files > 100 MB).
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

**Stickman-money niche (approved 2026-11-10)**, from `references/stickman-psychology/analysis.md`:

| Step | What | Done when |
|---|---|---|
| N1 | Niche isolation (§4a) | done: tests pass, old runs moved to `runs/skulsy-finance/` |
| N2 | Voice auditions: ~4 deep male + ~4 smooth female Kokoro voices, same paragraph | done: owner picked `af_kore` 0.9 |
| N3 | Stickman cast sheet: one fixed drawing-style prompt + cast (dad, mom, kids, grandparent, boss, worker) with simple identifiers; Meta AI via Chrome | done differently: owner chose no fixed cast; each story makes its own characters (style block + clothing identifiers, `style-stickman-calm`) |
| N4 | Style `stickman-calm`: Remotion folder, check_plan entry, skill (grey images, slow push-in/pan, ~0.4 s cross-dissolve, vignette, 2-line karaoke captions upper third, music + soft ambience, shots 2–7 s) | done: `runs/stickman-money/2026-11-10_two-brothers-paycheck` |
| N5 | Niche skill `niche-stickman-money`: formulas, 230–270 words, story numbers illustrative, real stats via facts.json, moral line + share cue, 100-idea topic bank | skill written; topic bank has 1 of 100 ideas |
| N6 | First 1:20–1:40 video | rendered 87.7 s; waiting on owner review + music |

## 13. If something breaks, look here

| Symptom | Where |
|---|---|
| Render hangs "Waiting for root component" | (a) Node 26 in use → `render.sh` uses Node 22; (b) Claude Code sandbox blocks headless Chrome ↔ local server → run the render outside the sandbox (`! engine/tools/render.sh runs/<niche>/<id>`) |
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
| 2026-11-09 | Cleanup: legacy `YouTubeAutomation/` and `experiments/` removed (Trash; legacy code in git `3c768e1`); prompts from the Style A test kept as `runs/2026-11-09_test-vintage-nvda/image_prompts.txt` | Owner asked to remove everything the project doesn't use |
| 2026-11-10 | v1.3: niche isolation: `niche.json` per niche (length, styles, banned) copied into each run; `new_run.py --niche` required; runs grouped as `runs/<niche>/`; check_plan/finish read the run's copy; banned list moved out of check_plan.py into niche.json; build steps N1–N6 for stickman-money | Owner starts a second niche (stickman money, 1:30) and asked for niches to be isolated; old hard-coded 2:00–2:48 rule would have refused every stickman video |
| 2026-11-10 | v1.3: style `stickman-calm` (Remotion: slow eased camera, 0.4 s cross-dissolve, vignette, 2-line karaoke captions with per-shot `captionTop`); `voice.py --sentence-gap` (voice each sentence, trim Kokoro's padding, add a fixed pause); check_plan `TAIL_DEFAULT` per style; skills `style-stickman-calm`, `niche-stickman-money` | Kokoro runs long text together (64 s, 236 wpm, no pauses); per-sentence calls alone added ~1 s padding each (117 s). Meta images put heads at 20–45% height, so captions moved from the reference's 23% to 15% |
| 2026-11-10 | AudioBed: music fades in 1 s and out over the last 2 s (all styles); first licensed track `okaya-whispers` in `library/music.json` | Track is 266 s, longer than videos: without a fade it stopped abruptly at the end |
| 2026-11-10 | Stickman blinks: `find_eyes.py` (numpy + scipy, already pinned) finds round head + two solid dots → `eyes.json`; renderer paints the eyes shut 4 frames every 2.8–4.5 s, inside the moving image layer. `clip` shots (animated video, ≤ clip length, up to 8.5 s) in stickman-calm. Root loads optional `eyes.json`; render.sh stages it. Topic bank: 100 seeds | Owner approved blinks + animated shots + story bank. Meta AI video isn't available in Claude's browser session, so clips come from the owner. Breathing skipped: needs characters cut out of the background |
| 2026-11-10 | v1.4: niche `strange-money` (true money stories, 45–70 s) + style `explainer-fast` (Remotion: 13 camera moves incl. CSS-3D tilts/orbits/dives, handheld wobble, 0.2 s dissolves, green-keyed cut-out **actors** with enter/idle motions, `fx` flash/shake/punch, 1–3-word captions at 70%, automatic whoosh per shot change). New tool `key_green.py` (numpy, no new package) + 4 tests; check_plan `check_explainer_shot` + 3 tests (47 total). `make_sfx.py`: 9 new generated sounds + 2 Kokoro crowd reactions; never overwrites existing files | Owner chose option B after the Ricks-clips analysis: the reference moves constantly inside every shot (animated 3D) and changes camera angle all the time; we get motion from camera moves + cut-out characters without new software. Blender (real 2.5D/3D) deferred until after draft 1 |
| 2026-11-10 | v1.5: explainer-fast **motion graphics** (`mg` per shot, `Graphics.tsx`: stamp, label, counter, arrow, money, speedLines, marks, cross, circle, pointer; own sound per graphic; `mgVolume`) and `bg` colour-card shots. Reuses flat-fastcut `Props.tsx` (arrow, money, speed lines). check_plan: graphic types/dirs/fields/words, caption-overlap warning, on-screen graphic numbers must be in facts.json; 4 tests (51 total) | Blender test looked crude (owner); Blender parked for R&D. Owner liked the flat-fastcut motion graphics and asked to try them over the AI pictures (trial; v2 kept) |
| 2026-11-10 | v1.5.1: explainer-fast graphics lose their own jitter/line boil; shot field `hold` delays a cut (0–0.6 s, renderer + checker lengths); checker: each graphic ≥ 1 s on screen | Owner: graphic effects collided with the shot wobble/shake, and cuts came before graphics could be seen |
| 2026-11-10 | v1.6: 47 recorded SFX (Mixkit free licence + freesound CC0) in `library/sfx/*_r*`; explainer-fast **sound pools** (`styles/explainer-fast/sounds.json`, read by the renderer and check_plan): a plan names a pool, the renderer picks a variant per shot/graphic; per-file gain; new default volumes from a measured voice-muted render | Owner: SFX must improve (generated sounds weak, Kokoro crowd robotic); same whoosh on every cut sounded repetitive |
