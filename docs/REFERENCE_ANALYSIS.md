# Reference Reel Analysis

Source files: `YouTubeAutomation/reference_reels/reel1/`, `reel2/` (videos + owner screenshots).
Measured with ffmpeg on 2026-11-09 (scene detection, contact sheets, EBU R128 loudness).
These numbers become the starting values for each style skill.

---

## Style A: "Mentor & Fool" vintage story (reel1, wolf + pig, Red Bull story)

| Property | Measured / observed |
|---|---|
| Length | 1:55 (115 s), 720×1280, 30 fps |
| Shots | ~55 distinct images; hard cuts at 0.3 threshold = 22, at 0.15 = 85 (includes in-shot motion) → **typical shot 1.5–3 s**, faster bursts (~0.3–0.5 s) in montage sections (57–72 s) |
| Structure | Present-day frame (wolf mentor + naive pig + raccoon cashier in a store) → **flashback history in monochrome** (1976 Thailand → Mateschitz → tests → can → marketing → bans → stunts → 14 billion cans) → back to present for the lesson → close-up of wolf with glowing eyes → black end card "WOLF" |
| Art | AI-generated, 1940s–50s cartoon look, thick outlines. Present = warm amber/sepia, interior lamps. Flashback = desaturated grey/sepia with grain. Consistent characters across shots |
| Motion | Shots are **image-to-video clips** (e.g. salesman closes briefcase, characters gesture), not static zooms |
| Captions | **One word at a time**, white serif caps (Times-like), soft shadow, lower-center (~78% height), small and calm |
| Audio | Integrated loudness **−16 LUFS**, LRA 4.2. Different voices per character, background ambience (store, crowd), vintage feel |
| Value | Real company history told as a story + one-line lesson at end |

## Style B: Flat 2D fast-cut comedy (reel2, RewRat channel)

| Property | Measured / observed |
|---|---|
| Length | 0:28, 720×1280, 24 fps |
| Shots | 28 cuts, **average shot 0.95 s**, 19 of 28 shots under 1 s |
| Art | Flat vector, thick black outlines, no shading, **solid background colour that changes almost every shot**. Simple box-head character, changes outfit/colour. Channel signature watermark |
| Motion | Pose swaps between frames (limited animation "on 2s/3s"), objects jump position, character **constant shake/jitter**, speed lines, spray particles, flash-to-white transition |
| Captions | One word at a time, white bold sans-serif, drop shadow, **dead center** of the screen |
| Audio | −18.4 LUFS, LRA 2.9. Fast SFX on nearly every cut |
| Value | Original character comedy; humor carries it |

## Feasibility in Remotion

- **Style B: yes, almost entirely.** Characters and props can be SVG/React components. Shake = small random offset/rotation per frame; "line boil" = SVG turbulence filter with a changing seed every 2–3 frames; speed lines, particles, flash transitions, word captions are all standard Remotion work. The hard part is **art volume** (~1 new drawing per second): needs a rigged character (swappable heads/expressions/arms) + a prop library, with Claude drawing simple SVG props and an image model for complex ones.
- **Style A: Remotion does the edit, not the art.** Shots need AI images + image-to-video (Meta AI) or 2.5D parallax. Remotion handles cuts, captions, colour grade (warm vs monochrome flashback), grain, vignette, transitions, SFX/music/ambience mixing. **Main risk: character consistency** across ~55 shots.
