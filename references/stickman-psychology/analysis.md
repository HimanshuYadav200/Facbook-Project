# Stickman reels: analysis (2026-11-10)

Source: 5 reels from one Facebook page (owner's notes: >2M views each, 3–4 posts/day, US audience).
Measured with ffmpeg (cuts, loudness) and mlx-whisper (transcripts, speaking rate). Transcripts are in the session log only (not saved here: they are someone else's scripts).

## 1. Numbers

| Reel | Length | Format | Hook (first line) | Words/min | Avg shot |
|---|---|---|---|---|---|
| 1 | 1:10 | "Science" claim about couples | "Men who regularly slap their girlfriend on the butt supposedly live much longer." | 171 | ~4.4 s |
| 2 | 1:25 | Second-person truth (to wives) | "Your husband is the only person in your life who loved you purely by choice." | 179 | ~4–8 s (slow zooms) |
| 3 | 1:23 | Parable (lawyer + teacher, plant + storm) | "A lawyer and a teacher lived next door to each other." | 186 | ~4.2 s |
| 4 | 2:58 | Listicle ("marriage has 6 stages") | "Most people think marriage fails because love disappears…" | 146 | ~4.1 s |
| 5 | 1:32 | Parable (father, son, $100) | "A father handed his 20-year-old son $100…" | 188 | ~3.7 s |

- All reels: 720×1280, 30 fps, **−14 LUFS** (same as our finish step).
- Engagement (owner): ~45k likes (2%), 400–600 comments, **4–6k shares**. That share count is high: people send these to their partner, child or parent. **Shareability is the main engine.**

## 2. Look (what makes the style)

- **Character:** blank round-head stickman. White body, dots for eyes, small mouth, no nose. Woman = same plus long hair and a dress. Kids = smaller copies. Faces carry the emotion (sad brows, smile, sweat drops).
- **Drawing:** grey pencil / marker on off-white. Furnished, fairly detailed rooms (sofa, lamp, plants, curtains). Reel 3 uses a different, heavier comic shading: **the page mixes image models**.
- **Colour:** nearly greyscale. A **warm accent** only where the story needs it (lamp glow, green dollar bill, sun). A soft **vignette** on every frame.
- **Symbols drawn into the scene:** brain sparks, heart line, circling arrows, puzzle piece, dashed arcs. These turn abstract psychology into a picture.
- **Motion:** none inside the drawing. A **slow push-in zoom** per shot and **soft cross-dissolves** between shots (ghost figures in mid-frames). Occasional dark/storm frames for drama.
- **Captions:** white bold rounded sans with a dark shadow, 1–2 lines, centred in the **upper third** (~y 22–30%). **Karaoke highlight**: the current word is yellow. A new line every 3–6 words.
- **Audio:** calm, slow male narrator (AI-sounding, US accent), meditation-style music under it, **no SFX**.

## 3. Script formulas (they repeat)

1. **Counter-intuitive "fact"** → biology words (dopamine, oxytocin) → a relationship takeaway → playful last line. *Reel 1's claims are made up ("microcardio impulse"). Risk: Facebook false-information penalties. We will not copy this part.*
2. **"Your husband/wife/mother…" truth** → list (parents… siblings… children…) → turn ("But your husband?") → warning → call to act ("Say thank you. Show affection.") → closing mirror line.
3. **Two-character parable**: two people, same start, different choices, a test (storm, earning $10) → the wise one explains → one-sentence moral → general life lesson.
4. **Numbered stages / signs**: hook promises a number + "most people fail at stage 3" (curiosity gap) → each stage = a name + 3–4 relatable sentences.

Every script ends on a **quotable moral line**. That line is what people share.

## 4. What we can do better than the reference

| Reference weakness | Our upgrade |
|---|---|
| Static slideshow | Subtle motion in Remotion: blinks, breathing, parallax layers, a slow hand-drawn line reveal on symbols |
| Inconsistent character (2 art styles) | One fixed character sheet. Every image prompt starts with it; contact-sheet check |
| Invented science | Psychology claims sourced (study + year) in `facts.json`, same rule as finance |
| No SFX, flat sound | Very soft ambience (pages, room tone, wind in the storm scene), ducked under the voice |
| Plain hook frame | A first frame built to stop the scroll (strong emotion + hook text) |
| Generic ending | A loop-back last line, and a "send this to…" cue that matches the share behaviour |

## 5. Fit with our engine

Close to the **vintage-story** pipeline: images, voice, slow camera, captions, music. Needs a new style, `style-stickman-calm`:
- new caption look (2-line karaoke, yellow active word, upper third);
- cross-dissolve and push-in;
- greyscale + vignette + accent;
- a **music bed** (we have none licensed yet: this becomes a blocker);
- a calm narrator (Kokoro audition: `am_michael`, `am_eric`, `am_onyx`, ~0.9 speed).

No new engine tools are expected. Details go to the architecture plan once the owner picks the niche.
