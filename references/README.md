# References: how to refine a niche or style

One folder per niche, e.g. `references/skulsy-finance/`. Put anything that shows what you want:

- screenshots of videos that perform well (name them if you can: `captions_like_this.png`)
- downloaded reels (`.mp4`)
- a `notes.md` with what you like / dislike ("cuts faster in the hook", "caption font like reel2")

Then tell Claude: *"refine skulsy-finance from references"*. Claude will:
1. measure the material (cut timing, colours, caption size, pacing) with ffmpeg;
2. write or update `analysis.md` in that folder;
3. propose exact changes to the style / niche skill in `.claude/skills/`;
4. apply them after you agree, and log the change in `docs/CONTEXT.md`.

Media files here are **not** pushed to GitHub (they may be other people's videos); only `.md` notes are.

Current material:
- `skulsy-finance/reel1_wolf_story/`: wolf + pig vintage story → style `vintage-story` (analysis: `docs/REFERENCE_ANALYSIS.md`)
- `skulsy-finance/reel2_rewrat_fastcut/`: RewRat flat 2D fast cuts → style `flat-fastcut`
- `stickman-psychology/`: 5 stickman relationship / moral-lesson reels (calm slideshow) → analysis in `stickman-psychology/analysis.md`; style + niche not decided yet
- `Ricks-clips/`: 5 fast animated explainer shorts (strange true stories, loopholes) → analysis in `Ricks-clips/analysis.md`; niche + style not decided yet (reel 2 has no audio)
