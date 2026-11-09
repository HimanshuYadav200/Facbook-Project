---
name: video-core
description: How every video in this project is made, step by step, with exact commands. Use whenever making, fixing, re-rendering or reviewing a video (any niche, any style), or when changing the engine. Load the niche skill (niche-*) and style skill (style-*) named in the run's brief together with this one.
---

# Video core: making one video

Read `docs/ARCHITECTURE.md` §2 for the why. This file is the how. Commands run from the project root.
`P=engine/.venv/bin/python` below means that Python (3.12 venv). Rendering needs Node 22 (render.sh sets it).

## Steps

| # | Step | Command / action | Output in `runs/<id>/` |
|---|---|---|---|
| 0 | New run | `P engine/tools/new_run.py <slug> --niche <n> --style <s>` | folder, `brief.md` |
| 1 | Brief + research | fill `brief.md`; decide **exact** tickers, series, dates | `brief.md` |
| 2 | Data | `P engine/tools/fetch_data.py prices <TICKER> runs/<id>/data/<name>.json` (also `fred`, `sec`, `crypto`) | `data/*.json` |
| 3 | Facts | `P engine/tools/finance_calc.py invest/change/drawdown/cagr/inflate ... --id <id>` → add each to `facts.json` | `facts.json` |
| 4 | Script | write `script.txt` following the niche skill; **only numbers from facts.json `say`** | `script.txt` |
| 5 | Voice | `P engine/tools/voice.py runs/<id> --voice <v> --speed <s>` (voice/speed from niche skill) | `voice.wav`, `words.json` |
| 6 | Plan | write `plan.json` (schema: `references/plan-schema.md`, style fields: style skill); `image_prompts.txt` if the style uses images | `plan.json` |
| 7 | Images | default: Claude makes them on meta.ai via Claude in Chrome (see style skill). Manual option: owner runs the Meta extension. Files land in `incoming/` → `P engine/tools/match_images.py runs/<id>` | `img/` |
| 8 | Check | `P engine/tools/check_plan.py runs/<id>` → fix every ERROR | |
| 9 | Render | `engine/tools/render.sh runs/<id>` (`--preview` = half size, faster) | `out/raw.mp4` |
| 10 | Finish | `P engine/tools/finish.py runs/<id>` (−14 LUFS, length, black frames) | `out/final.mp4` |
| 11 | Review | `P engine/tools/contact_sheet.py runs/<id>` → read sheets + `sheets.txt` with `references/review-checklist.md`; fix plan → back to 8. **Max 2 rounds** | `review/` |
| 12 | Facts review + upload text | `P engine/tools/facts_review.py runs/<id>` → `review/facts_review.md` for the owner; write `upload.md` (title, description, hashtags, "Not financial advice.") | |

Short test clips: add `--test` to check_plan.py and finish.py (skips the 2:00–2:48 rule).

## Rules that apply to every video

1. **Numbers.** Never write a number from memory or a search snippet. Fetch → calculate → `facts.json` → script. Write amounts as digits (`$41,100`, `66%`). `check_plan.py` enforces this. Details: `references/data-honesty.md`.
2. **Explain, don't decorate.** Every teaching beat (chart, comparison, counter) passes the explanation test and has a `teach` line in the plan. Details: `references/explain-rules.md`.
3. **Voice before plan.** Shots are anchored to word indexes in `words.json`. If the script changes, re-run voice.py, then fix the plan's indexes.
4. **Characters are owned assets** (`library/characters/`), not regenerated per video.
5. **Log** what was done in the run's `log.md`. Engine or skill changes go in `docs/CONTEXT.md` (and `docs/ARCHITECTURE.md` if structural).
6. **Token budget:** one contact-sheet pass per review round, max 2 rounds. Don't re-read big files you already have.

## When something fails
`references/known-errors.md`, then `docs/ARCHITECTURE.md` §13.
