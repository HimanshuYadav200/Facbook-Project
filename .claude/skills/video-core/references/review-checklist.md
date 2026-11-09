# Review checklist (step 11)

Inputs: `review/sheet_N.jpg` (40 shots per sheet, left→right, top→bottom) + `review/sheets.txt` (tile → shot, time, length, words).
Budget: read each sheet once per round; max 2 fix rounds. Write findings to `review/round_N.md`.

## Per tile
- [ ] Picture matches the words said (sheets.txt line) — no unrelated filler.
- [ ] Teaching shots: the change is visible and labelled (explanation test).
- [ ] **On-screen numbers** (charts, stickers, signs, numbers drawn inside AI images) match `facts.json`. Meta AI invents numbers: cover wrong ones with an overlay or swap the image.
- [ ] Captions readable, not covering the key part of the image.
- [ ] Character looks consistent (same Skulsy design).
- [ ] No AI artefacts that look broken (hands, extra limbs, garbled text) in the frame's focus.
- [ ] No black or empty frames (finish.py also checks).

## Whole video
- [ ] Hook in the first 3 s states a specific situation or number.
- [ ] Pace matches the style (shot lengths in sheets.txt).
- [ ] SFX on cuts as the style says; music/beds not louder than voice (listen to 10 s at start, middle, end).
- [ ] finish.py reported −14 ±1 LUFS, length 2:00–2:48, no black frames.
- [ ] `facts_review.md` and `upload.md` written; manual-check facts listed first.
