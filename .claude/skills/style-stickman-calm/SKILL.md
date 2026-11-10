---
name: style-stickman-calm
description: Look and pacing of the "stickman-calm" style (grey pencil-sketch stickman images, slow camera, soft cross-dissolves, 2-line karaoke captions, calm narration + music). Use when writing plan.json or image prompts for a run whose style is stickman-calm (any stickman niche), or when refining this style from references.
---

# Style: stickman-calm

Based on 5 viral stickman reels (`references/stickman-psychology/analysis.md`). Renderer: `engine/remotion/src/styles/stickman-calm/StickmanCalm.tsx`. Known-good example: `examples/plan.json` (first video, `runs/stickman-money/2026-11-10_two-brothers-paycheck/`).

## Measured targets
| Thing | Target | Source |
|---|---|---|
| Shot length | ~3.5–5 s typical; hard limits 2–7 s | reels: 3.7–4.4 s average |
| Shots per video | ~20–24 for 1:30 (one per sentence or two) | |
| Narration | ~175 words/min with a breath between sentences: `voice.py --sentence-gap 0.45` | reels 146–188 wpm |
| Captions | built in: 2-line phrases, words appear as spoken, current word yellow, Arial Rounded Bold 62 px, at 15% height | reels |
| Transitions | 0.4 s cross-dissolve, built in; no hard cuts | reels |
| Blinks | built in: every face blinks (4 frames, every 2.8–4.5 s) once `find_eyes.py` has run | our upgrade |
| Sound | voice + calm music (`the-end-soundaudio` at 0.08; fades in/out built in); no SFX on cuts (an optional very soft `sfx` per shot plays at 0.12) | reels: no SFX |
| Loudness | −14 LUFS (reels are −14.2) | |

## Shot fields
| Field | Values |
|---|---|
| `type` | `"image"` (still + camera move + blinks) or `"clip"` (animated video, e.g. Meta AI animate, 5–8 s) |
| `clip` | clip shots: video file in `img/` (e.g. `01_first_day.mp4`). The shot may not last longer than the clip (check_plan refuses); clip shots may run up to 8.5 s. No camera move unless `motion` is set |
| `img` | file in `img/` |
| `motion` | `pushIn` (default) / `pullOut` / `panL` / `panR` / `panUp` / `panDown`: slow and eased. Vary it; never 3 of the same in a row |
| `zoom` (default 1.04), `focus` [x, y] 0–1 (default [0.5, 0.45]) | |
| `captionTop` | 0–1, default 0.15. Close-ups where a head fills the top: move the caption lower (e.g. 0.68) |
| `sfx` | optional, very soft |
Plan level: `music`, `beds`, `tailSeconds` (default 1.0; ~1.2 lets the last line breathe), `notes`.

## Blinks (after images are in `img/`)
`P engine/tools/find_eyes.py runs/<niche>/<id>` → `eyes.json` + `review/eyes_check.jpg`. Look at the check sheet once: a red mark must sit on each eye. Faces it can't read (closed eyes, odd close-ups) get no blink, which is fine. A wrong mark: delete that image's entry in `eyes.json`.

## Animated clips (optional)
Meta AI video was **not available** to Claude's browser session (2026-11-10: "Video generation isn't available to you"). The owner makes clips (5–8 s) and drops them in `img/`; use them for 2–4 key shots (hook, turn, ending). Re-time the cut so the shot fits inside the clip.

## Images (Meta AI, via Claude in Chrome)
- One meta.ai chat per video keeps the cast consistent. The first prompt carries the full style + cast; later prompts start "Next image, vertical 9:16, exact same pencil sketch style and same characters, no text, no numbers: …". Meta returns 1152×2048.
- **Style block** (first prompt): "Black and white pencil sketch illustration, vertical 9:16. Simple stickman characters with big round blank white heads, two small dot eyes, a small mouth, no nose, no hair (women have long hair), smooth white bodies with soft grey shading. Clean, detailed hand-drawn background in light grey. Soft vignette. No text, no words, no letters, no numbers, no logos anywhere."
- **Cast:** the niche skill's cast list; every character gets one clothing identifier (blazer + watch, hoodie + backpack, glasses, apron…) repeated in every prompt that shows them.
- **Keep the top 20% simple** (sky, wall): ask for "characters in the lower two thirds" so captions don't sit on faces.
- A little warm colour (lamp glow, sunrise) is welcome; Meta adds it by itself.
- Save with a page helper that fetches the newest large image and downloads it as `skm_<name>.webp` (worked in the first video: ~30 s per image, 2 images per browser batch to avoid time-outs). Then move into `incoming/` and run `match_images.py`.
- Check the contact sheet for invented numbers or text (money bills, calculators, clocks).
