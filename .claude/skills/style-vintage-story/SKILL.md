---
name: style-vintage-story
description: Look and pacing of the "vintage-story" style (old-film narrated story, 1940s cartoon images, real-data paper charts, one-word serif captions). Use when writing plan.json or image prompts for a run whose style is vintage-story, or when refining this style from references.
---

# Style: vintage-story

Based on reference reel 1 (wolf + pig Red Bull story; `references/skulsy-finance/reel1_wolf_story/`, measured in `docs/REFERENCE_ANALYSIS.md`). Renderer: `engine/remotion/src/styles/vintage-story/`. Known-good example: `examples/plan.json`.

## Measured targets
| Thing | Target | Source |
|---|---|---|
| Shot length | typical 1.5–3 s; montage bursts 0.5–1 s; hard limits 0.5–7 s | reel 1 |
| Shots per video | ~60–80 for 2:30 | reel 1: ~55 in 1:55 |
| Narration pace | `bm_george` at 0.95 ≈ **2.0 words/s** → 2:00–2:48 ≈ **240–335 words** | test run |
| Captions | one word, white serif caps, soft shadow, at 80% height (built in) | reel 1 |
| Loudness | finished at −14 LUFS (reel 1 is −16) | |
| Structure | present day → **flashback in monochrome** → back to present for the lesson → end card | reel 1 |

## Look
- **Past = `grade: "mono"`** (sepia/grey), **present = `grade: "warm"`**. Switch grade when the story's time switches.
- Every shot moves: `motion` pushIn / pullOut / panL / panR / panUp / panDown, with `focus` on the subject. Never two identical motions in a row.
- Year cards: `stamp: "JAN 2016"` on the first shot of each new period.
- `flash: true` + `shake: true` for shocks (a crash, a reveal). Use sparingly: ≤ 1 per 20 s.
- `sticker: {text, x, y}` for a key number over an image (must be a facts.json `say`).
- Beds: `vinyl` 0.35 + `room` 0.4. End card `{"text": "SKULSY", "seconds": 2}`.

## Shot fields
| Field | Shot type | Values |
|---|---|---|
| `type` | all | `image` or `chart` |
| `img` | image | file name in `img/`, e.g. `01_office.webp` |
| `motion`, `zoom` (1 = full frame, 1.05–2.2), `focus` [x,y] 0–1 | image | |
| `grade` | image | `mono` / `warm` |
| `stamp`, `sticker`, `flash`, `shake` | image | see Look |
| `chart`, `to` (YYYY-MM-DD), `color` (ink/red/gold), `teach` | chart | `chart` names an entry in plan `charts` |
| `sfx`, `cues: [{word, sfx}]` | all | `cues` = extra SFX on a word (e.g. `cash` on a number) |

Plan-level `charts`: `{"<id>": {"data": "<data name>", "amount": 1000, "start": "YYYY-MM-DD", "title": "$1,000 IN NVIDIA", "subtitle": "invested January 2016"}}`. Each chart shot continues the line from where the previous shot of that chart stopped; the counter shows `amount × price / start price` (same maths as finance_calc `invest`). Chart dates must use the same start date as the facts.

## SFX habits
`whoosh` on most image cuts, `thud` on stamps, `tick` on small moves, `cash` cue on money numbers, `crash` on drops, `ding` on the reveal.

## Images (Meta AI)
- One meta.ai chat per video (keeps Skulsy consistent); ~30 s between prompts; download each with the page script (details: `references/meta-ai.md`).
- `image_prompts.txt`: `<name>: <prompt>` per line. Prompt template:
  `<scene with Skulsy, the friendly cartoon skeleton with a round white skull, big dark eye sockets and a wide grin, brown three-piece suit, green tie, grey bowler hat>, 1940s vintage cartoon style, thick ink outlines, <black and white sepia | warm amber lamplight>, film grain, vertical 9:16`
- **No numbers or text in prompts** (Meta AI invents wrong ones). Put numbers on screen with `sticker`/charts instead.
- Refused prompt → use Meta's suggested alternative, then check it still fits the words.
