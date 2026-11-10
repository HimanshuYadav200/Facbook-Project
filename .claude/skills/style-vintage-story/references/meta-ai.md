# Getting images from Meta AI (what worked in the tests, 2026-11-09)

Default path: Claude drives meta.ai via Claude in Chrome. Manual option: owner runs the Meta Automation extension (it can't be driven by Claude) with the same prompts; files land in the run's incoming/.

- Start Claude Code with `claude --chrome`; be logged into meta.ai.
- Type each prompt into one meta.ai chat ("Create the next image, same Skulsy character…"); one chat keeps the character consistent.
- Wait ~30 s per image before sending the next one, or Meta AI skips it.
- Save with a small page script (fetch the image, download it with a fixed name). Chrome must be allowed to download multiple files from meta.ai.
- Meta AI only keeps the newest 2 images loaded, and some follow-ups become "edits" with the old image layered underneath. Always check saved files for duplicates (`md5`).
- The Meta Automation side panel can't be driven by Claude in Chrome (extensions can't control each other).

- After downloading: move files into the run's `incoming/`, then `engine/.venv/bin/python engine/tools/match_images.py runs/<niche>/<id>`.
