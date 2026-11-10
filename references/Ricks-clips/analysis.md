# Ricks-clips reels: analysis (2026-11-10)

Source: 5 YouTube Shorts from one channel (owner's notes: millions of views, thousands of shares and comments, 1 post/day).
Measured with ffmpeg + numpy (shot changes, loudness, sound hits) and mlx-whisper (transcripts, speaking rate).
Transcripts stay in the session log only (they are someone else's scripts).
Reel 2's download has **no audio track**: picture only.

## 1. Numbers

| Reel | Topic | Length | Words/min | Shots | Median shot | Sound hits/min |
|---|---|---|---|---|---|---|
| 1 | Why railroads have gaps (heat expansion) | 1:05 | 201 | ~28 | 1.7 s | ~17 |
| 2 | The pink prison cell (colour calms inmates) | 1:05 | (no audio) | ~26 | 1.9 s | – |
| 3 | Ancient Chinese earthquake jar (seismoscope) | 1:05 | 218 | ~27 | 2.0 s | ~25 |
| 4 | Japan's pachinko loophole (prize-shop window) | 0:45 | 215 | ~13 | 2.6 s | ~31 |
| 5 | Burglar who moved furniture 1 inch (twist: house scam) | 0:58 | 244 | ~24 | 1.8 s | ~37 |

- 1080×1920 or 720×1280, 30 fps, **−14 LUFS** (same as our finish step).
- Shot counts are a lower bound: changes are soft dissolves, and shots in the same room look alike. Viewing the frames at 4 fps gives **about one new shot every 1.5–2 s**.
- **Shots are not under 1 second** (owner's note said < 1 s). They *feel* faster because nothing is ever still: the camera moves and the characters act inside every shot.

## 2. Look

- **Stylised 3D world** (game-like lighting, depth, soft shadows, rich colour: canyon reds, prison pinks, neon Tokyo, warm living rooms).
- **Characters:** round white heads, dot or ring eyes, thin black stick legs, simple clothes and props (caps, uniforms, masks). A new cast per story; the hero changes every video.
- **Motion inside the shot (this is the key):** characters walk, turn, gesture and change expressions; effects grow (cracks, steam, flashes); the camera dollies, orbits, pushes in, looks down from above. Very little is a still picture.
- **Transitions:** a quick dissolve (~0.2 s) or a camera move into the next shot. No hard cuts.
- **Captions:** **1–3 words at a time**, white heavy sans with a black outline and shadow, centred at ~**70% height** (lower third, under the faces). No colour highlight.
- **Frame 1:** the hero mid-action, already in the scene; the first spoken line is the hook.

## 3. Sound

- Voice: young, bright, excited storyteller (joy, wonder, a laugh in the mocking lines), **200–245 wpm**: much faster than stickman (175).
- Almost no pauses (5–13 in a minute).
- Music: very low and almost hidden. In the pauses, music + SFX sit **~7–14 dB under the voice**.
- SFX: **about one hit per shot** (17–37/min): whooshes on transitions, pops, impacts and themed sounds (train clack, crowd laugh, alarm). Always under the voice.

## 4. Script formula (all 5 reels)

1. **Hook = one strange action, stated flatly:** "He sawed gaps into a railroad every 39 feet." No question, no "did you know".
2. **"You see,"**: 1–2 lines of context (the stakes, the rival).
3. **Mockery / doubt:** the boss, the court or the police laughs; a short quoted line of dialogue.
4. **Escalation with time markers:** "Weeks later…", "By July…", "Then one night…".
5. **The payoff:** the strange thing turns out to be right, often by **saving or costing a lot of money or lives**.
6. **Mechanism in 1–2 sentences:** how it works (heat expansion, pendulum, a separate shop). This is the "aha" people share.
7. No moral and no call to action. It ends on the reveal.

Topics: real engineering, history and **loopholes** (pachinko is a money loophole). Reel 5 is fiction told as fact.

## 5. What we can do better

| Reference weakness | Our upgrade |
|---|---|
| Reel 5 presents fiction as true | True stories only, sources in `facts.json` (protects against YouTube/Meta misinformation rules) |
| No source for the "aha" claims | A source line in the description |
| Music almost inaudible | A light bed set ~12 dB under the voice (as in stickman) |
| One look for all topics | Our own character design (we must **not** copy Rick's characters or look: Meta "unoriginal content" risk) |

## 6. Fit with our engine (the hard part)

The reference is **animated 3D** (each shot moves inside itself). One person posting daily suggests AI video tools or a reused 3D asset kit. Our engine makes **still images + camera moves**. Three ways to close the gap:

| Option | What it is | Quality vs reference | Cost / effort |
|---|---|---|---|
| **A. Images + strong motion graphics** | ~35 Meta AI images in a stylised-3D cartoon look; Remotion adds fast eased camera moves, shake, wobble, punch-zooms, speed ramps, whip/dissolve transitions, effect overlays (flash, dust, speed lines), and 1–3-word captions; SFX on every shot | ~60–70%: lively, but characters don't act | Free; fully automatic (like stickman) |
| **B. A + cut-out characters** | Characters made on a flat green background, keyed out in Remotion, placed over the scene: they bounce, squash, lean, slide in, blink. Two layers give parallax depth | ~75%: characters move and react | Free; no new package (green-key is a Remotion/CSS filter or an ffmpeg `colorkey`); more images per video |
| **C. B + AI video clips for key shots** | 3–6 animated clips (hook, payoff) made by the owner in Meta AI / another video tool; our `clip` shot type already plays them | ~85–90% | Owner time per video; paid tool if Meta animate isn't enough |

SFX: we have 10 simple self-made sounds (`library/sfx`). For "better SFX", either add a **free CC0 pack** (Kenney.nl, Freesound CC0; owner downloads; licence entry in `sfx.json`) or extend our generator (`make_sfx.py`) with richer whooshes, risers and impacts. A themed hit per shot (train, crowd, alarm) needs the CC0 pack.
