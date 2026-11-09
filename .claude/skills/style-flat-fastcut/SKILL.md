---
name: style-flat-fastcut
description: Look and pacing of the "flat-fastcut" style (flat 2D comedy drawn in code, Skulsy SVG rig, cut every ~0.9 s, SFX on every cut, bold centred one-word captions). Use when writing plan.json for a run whose style is flat-fastcut, or when refining this style from references.
---

# Style: flat-fastcut

Based on reference reel 2 (RewRat; `references/skulsy-finance/reel2_rewrat_fastcut/`, measured in `docs/REFERENCE_ANALYSIS.md`). Renderer: `engine/remotion/src/styles/flat-fastcut/` (Skulsy rig `Skulsy.tsx`, props `Props.tsx`). Known-good example: `examples/plan.json`. No images to generate: everything is drawn in code (zero image tokens).

## Measured targets
| Thing | Target | Source |
|---|---|---|
| Shot length | **average ~0.9 s**, most under 1 s; limits 0.25–2.5 s (last shot up to 4 s) | reel 2: avg 0.95 s, 19/28 under 1 s |
| Shots per video | ~150–180 for 2:30 (plan in sections of ~30 shots to keep it manageable) | |
| Narration pace | `am_puck` at 1.1 ≈ **3.3 words/s** → 2:00–2:48 ≈ **390–550 words** | test run |
| Background | **solid colour that changes almost every shot** | reel 2 |
| Captions | one word, white bold sans, black stroke, dead centre (built in, 44% height) | reel 2 |
| SFX | on nearly every cut | reel 2 |

## Shot fields
| Field | Values |
|---|---|
| `bg` | hex colour; change it nearly every shot. Dark red `#5a1e1e` = loss, green `#2f8f46` = gain, yellow `#f2df7c` = neutral/happy |
| `shake` | 0–3 camera shake (2–3 for shocks) |
| `speedLines` | true for fast moments |
| `push` | slow zoom-in to keep a longer shot alive |
| `layers` | list of `{type, x, y, w, h, enter, props}` placed by centre in 1080×1920 |

Layer types and props:
| type | props |
|---|---|
| `skulsy` | `expression`: happy / normal / shocked / panic / smug / crying; `leftArm`, `rightArm`: degrees (0 down, 90 out, 160 raised); `holding`: `money` / `phone-up` / `phone-down` / `phone-flat`; `hoodie` colour |
| `phone` | `trend`: up / down / flat |
| `arrow` | `dir`: up / down |
| `money` | `count`: 1–5 bills |
| `sign` | `lines`: 1–2 short lines, `bg` colour. Numbers on signs must be facts.json `say` values |
| `grandma` | `asleep`: true/false |

`enter`: pop / drop / rise / slideL / slideR / none. Skulsy is ~620×1085 when he's the subject.

## Rhythm
- One idea per shot; cut on the spoken word the picture shows.
- Fast one-word lines ("Sold. Up. Bought. Down.") are where Whisper timings are least precise: give each its own shot only if words are ≥ 0.3 s apart, otherwise merge (check_plan refuses shots under 0.25 s).
- SFX: `pop` on appear, `whoosh` on movement, `thud`/`crash` on loss, `cash` on money, `boing` on mistakes, `ding` on the lesson.
- End on the lesson as a sign (up to 4 s hold).
- **Keep signs and the phone out of the caption band** (y 760–930, the caption sits at 44% height): put signs at y ≈ 450–650 or ≥ 1100. check_plan warns when they overlap (seen in the first test: "NEXT MORNING" sign under the caption).

## Teaching beats
This style is comedy-first; numbers still need a teaching visual (sign with the number + arrow/phone trend) and a `teach` line on that shot. New chart-type visuals for this style = a new layer type in `Props.tsx` (propose it first).
