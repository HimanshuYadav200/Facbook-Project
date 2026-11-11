---
name: style-explainer-fast
description: Look and pacing of the "explainer-fast" style (stylised 3D cartoon images, a new picture every ~1.5-2 s, constant camera motion incl. 3D tilts/orbits/dives, green-keyed cut-out characters that pop in and move, 1-3-word captions in the lower third, a whoosh on every shot change). Use when writing plan.json or image prompts for a run whose style is explainer-fast, or when refining this style from references.
---

# Style: explainer-fast

Based on `references/Ricks-clips/analysis.md`. Renderer: `engine/remotion/src/styles/explainer-fast/ExplainerFast.tsx`. Known-good example: `examples/plan.json` (draft 1, `runs/strange-money/2026-11-10_eiffel-tower-sale/`).

## Measured targets
| Thing | Target | Source |
|---|---|---|
| Shot length | median ~1.6–2 s; hard limits 0.7–4 s (last ≤ 4 s) | reels: median 1.7–2.6 s, dissolves |
| Shots | ~30–35 for a 55 s video | |
| Transitions | 0.2 s dissolve, built in | reels |
| Motion | **every shot moves**: a camera move (eased: fast start, soft stop) + handheld wobble, built in | reels: nothing is ever still |
| Captions | built in: 1–3 words, Arial Black 84 px, white with thick black outline, pop-in, at 70% height | reels |
| Sound | built in: a soft recorded whoosh on **every other** shot change (`cutSfxVolume`, default 0.14); stamps, counters, money, crosses and circles have their own sound (`mgVolume` 0.25), labels/arrows/?!/pointers are silent; themed `sfx` per shot (`sfxVolume` 0.22). Music very low (0.05). Owner 2026-11-11: fewer, quieter, realistic sounds (no cartoon pops/boings) | reels: ~1 hit per shot, 7–14 dB under the voice |
| Narration | ~210–240 wpm, no sentence gap | reels 200–245 wpm |

## Shot fields
| Field | Values |
|---|---|
| `img` | background or full scene in `img/` (required) |
| `cam` | `pushIn` `pullOut` `craneDown` `craneUp` `panL` `panR` `tiltDown` `tiltUp` `orbitL` `orbitR` `dive` `roll` `whip` (default: cycles through the list). **Never the same twice in a row**; mix 3D ones (tilt, orbit, dive) with flat ones |
| `zoom` (default 1), `focus` [x, y] 0–1 | `focus` = the point the camera moves around (e.g. [0.5, 0.78] when the subject is low in the picture) |
| `actors` | list of cut-outs over the scene (see below) |
| `fx` | any of `flash` (white flash in), `shake` (a hit that settles), `punch` (quick zoom kick) |
| `sfx`, `sfxVolume` (0.22) | extra sound at the shot start, **only on story beats** (a reveal, a door, a gasp, the payoff): about 1 in 3 shots. Use a **pool** from `engine/remotion/src/styles/explainer-fast/sounds.json` (realistic: `impact`, `tension`, `swell`, `sting`, `paper`, `writing`, `typewriter`, `gavel`, `vault`, `door`, `bills`, `cash`, `coins`, `camera`, `press`, `phone`, `siren`, `handcuffs`, `heartbeat`, `gasp`, `crowd_whoa`, `crowd_murmur`, `crowd_laugh`, `applause` …; the renderer picks a recorded variant) or an exact file in `library/sfx`. For a sound the story needs and the library lacks, make one: `P engine/tools/gen_sfx.py <run-slug>_<what> "<realistic foley description>" --seconds 2` (local Stable Audio 3; listen once before using). Avoid `boing`, `pop`, `sparkle` (cartoonish) |
| `cutSfx` | override the automatic whoosh (pool or file; `null` = none). Default: on every other cut only, `whoosh` pool (soft), `dive` for dive/craneDown, `whip` for whip; set it to force a whoosh on an important cut |
| `captionY` | 0.05–0.9, default 0.7 |
| `bg` | instead of `img`: a flat colour card (e.g. `"#2f8f46"`) for a graphics-only shot, like the flat-fastcut test |
| `mg` | motion graphics over the shot (see below) |
| `hold` | 0–0.6 s: this shot's cut comes that long after its word, so the previous shot's graphic can be read |

**Actor** = `{img, x, y, h, enter?, idle?, at?, flip?}`: `img` a PNG made by `key_green.py`; `x`,`y` = feet position (shares of the frame); `h` = height (share; ~0.5); `enter` `pop` (default) / `slideL` / `slideR` / `drop` / `none`; `idle` `breathe` (default) / `bob` / `wobble` / `hop` / `shake` / `lean` / `none`; `at` = word index when it appears (inside the shot).

**Motion graphic** (`mg`) = `{type, x?, y?, size?, at?, text?, to?, dir?, rot?, sfx?}` (renderer: `Graphics.tsx`). `x`,`y` = centre (pointer: the tip), shares of the frame (default x 0.5, y 0.3); `size` = width share; `at` = word index; some types play a sound (`sfx` overrides, `null` = none; plan `mgVolume`, default 0.25).
| type | what | default sound |
|---|---|---|
| `stamp` (`text`, `rot`) | red rubber stamp slamming down ("SOLD!", "FAKE") | impact |
| `label` (`text`) | cream tag card ("1925", "Victor Lustig"); over 14 letters it breaks into 2 lines (keep it under ~30) | – |
| `counter` (`to`, `text`) | number counting up in 0.8 s, then lands ("7,300 / tons of iron") | ticks + ding |
| `arrow` (`dir` up/down) | big bouncing arrow | – |
| `money` (`dir` rain/left/right, `y` = height of the band for left/right) | banknotes tumbling | cash |
| `speedLines` | white streaks across the frame | – |
| `marks` (`text`, default "?!") | big yellow ?! wobbling | – |
| `cross`, `circle`, `pointer` (`dir` = side it comes from) | red X / hand-drawn loop / arrow at a spot in the picture; these move with the camera | thud / writing / – |

Graphics have no wobble of their own (they ride the shot's wobble/shake; owner: effects must not fight). **Every graphic must stay ≥ 1 s on screen** (checker error; fix by an earlier `at` and/or `hold` 0.2–0.4 on the next shot). Rules: text graphics high (y ≤ 0.45; the checker warns near the caption); numbers on them must be in `facts.json` (checked); about one graphic per 1–2 shots, on the word it illustrates; don't repeat the caption word for word every time.

## Images (Meta AI, via Claude in Chrome)
- One chat per video. First prompt: the **style block** + "I will ask for many images in this exact same style". Later: "Next image, vertical 9:16, exact same 3D cartoon style and character design, no text, no numbers: …". 2 images per browser batch, wait ~38 s each (a slow image arrives late and shows up as "2 new candidates": save it under the earlier name).
- **Style block:** "Stylized 3D cartoon render, vertical 9:16, like a cozy animated movie or a miniature diorama: soft global illumination, warm rich saturated colours, rounded chunky shapes, slight depth of field. Characters are cute simple cartoon people with big round cream-coloured heads, small black dot eyes, simple eyebrows, small mouths, no nose, short rounded bean-shaped bodies. No text, no letters, no numbers, no logos." (Our own look: not Rick's white heads on stick legs.)
- Three kinds of image: `s_*` full scenes (characters inside), `bg_*` empty backgrounds with "open space in the lower middle" (for actors), `g_*` actors: "… standing alone on a plain flat solid bright green background (#00FF00), full body, whole figure visible, no shadow, no floor, nothing else in the image". **No green clothes** on anyone.
- Ask for **angles** to give the cut variety: low angle, top-down, close-up, under-the-table, aerial.
- Save with `engine/tools/meta_save.js` (video-core step 7); `match_images.py` puts `g_*` files in `img/green/` by itself (accepts `name: prompt` and `name | prompt` lines). Then `P engine/tools/key_green.py runs/<niche>/<id>` → `img/g_*.png` + `review/green_check.jpg` (check: no green fringe, no holes).
- Check the contact sheet for invented text/numbers (signs, door numbers).

## Not yet (draft 1)
Blinks on actors, real 3D (Blender: parked for R&D, see docs/CONTEXT.md), themed sounds beyond our generated set, AI video clips.
