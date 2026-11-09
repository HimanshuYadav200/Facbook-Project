# Experiments: style test clips

Throwaway test area for checking what quality each style can reach. Not the final engine.
The legacy project in `YouTubeAutomation/` is untouched.

## Layout

| Path | What it is |
|---|---|
| `.venv/` | Python 3.12 environment (Kokoro TTS, mlx-whisper, torch). Python 3.14 is too new for these libraries |
| `tools/voice_and_timing.py` | Script text → `voice.wav` (Kokoro) → `words.json` (word timings from mlx-whisper). Caption words always come from the script; Whisper only gives timing |
| `tools/make_sfx.py` | Generates placeholder sound effects from code (whoosh, pop, thud, ding, boing, crash, tick, cash, vinyl, room) |
| `tools/finalize.sh` | Normalizes loudness to −14 LUFS for social platforms |
| `remotion/` | Remotion project (pinned 4.0.537, React 18). **Needs Node 22** |
| `remotion/public/<style>/plan.json` | The edit plan: shots tied to word positions, layers, entrances, SFX. This is what the Claude "brain" writes |
| `remotion/src/styleB/` | Flat 2D renderer: Skulsy SVG rig, props, wobble/shake/boil, captions |
| `styleA_test/` | Vintage narrated test: script, Meta AI prompts, `incoming/` drop folder for generated images |
| `out/` | Rendered test videos |

## Run Style B again

```zsh
cd experiments
.venv/bin/python tools/voice_and_timing.py styleB_test/script.txt remotion/public/styleB am_puck 1.1
cd remotion && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx remotion render src/index.ts StyleB ../out/styleB_raw.mp4
cd .. && tools/finalize.sh out/styleB_raw.mp4 out/styleB_v2.mp4
```

## Run Style A again

```zsh
cd experiments
.venv/bin/python tools/voice_and_timing.py styleA_test/script.txt remotion/public/styleA bm_george 0.95
cd remotion && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npx remotion render src/index.ts StyleA ../out/styleA_raw.mp4
cd .. && tools/finalize.sh out/styleA_raw.mp4 out/styleA_v2.mp4
```

Images: `styleA_test/incoming/` (from Meta AI) copied to `remotion/public/styleA/img/`. Chart data: `remotion/public/styleA/nvda.json` (Alpha Vantage, split/dividend adjusted).

### Getting images from Meta AI through Claude in Chrome (what worked)
- Start Claude Code with `claude --chrome`; be logged into meta.ai.
- Type each prompt into one meta.ai chat ("Create the next image, same Skulsy character…"); one chat keeps the character consistent.
- Wait ~30 s per image before sending the next one, or Meta AI skips it.
- Save with a small page script (fetch the image, download it with a fixed name). Chrome must be allowed to download multiple files from meta.ai.
- Meta AI only keeps the newest 2 images loaded, and some follow-ups become "edits" with the old image layered underneath. Always check saved files for duplicates (`md5`).
- The Meta Automation side panel can't be driven by Claude in Chrome (extensions can't control each other).

Preview/edit live in the browser: `cd remotion && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run studio`

## Known gotchas

- **Node 26 hangs Remotion** ("Waiting for root component to load"). Always use Node 22 via the PATH prefix above.
- Whisper misspells names ("Skulsy" → "Skulce"); fixed by aligning to the script text.
