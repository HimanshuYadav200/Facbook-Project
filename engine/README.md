# Engine

The code that turns a run folder into a finished video. How to *use* it step by step: `.claude/skills/video-core/SKILL.md`. Why it's built this way: `docs/ARCHITECTURE.md`.

## Setup (once)
```zsh
/opt/homebrew/bin/python3.12 -m venv engine/.venv
engine/.venv/bin/pip install -r engine/requirements.txt
cd engine/remotion && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm ci
engine/.venv/bin/python engine/tools/make_sfx.py          # placeholder SFX into library/sfx
```
Keys in the project `.env`: `ALPHA_VANTAGE_API_KEY`, `FRED_API_KEY`, `TIINGO_API_KEY` (daily prices), `SEC_USER_AGENT` ("Name email", for SEC data).

## Tools (`engine/tools/`, each does one job, each has `--help`)
| Tool | Job |
|---|---|
| `new_run.py` | create `runs/<niche>/<date>_<slug>/` with a copy of the niche's `niche.json` (`--niche` required) |
| `fetch_data.py` | official data → `data/*.json` (Tiingo, Alpha Vantage, FRED, SEC) |
| `finance_calc.py` | numbers for facts.json (invest, change, drawdown, cagr, inflate) |
| `find_eyes.py` | images → `eyes.json` (stickman eye positions for blinking) + `review/eyes_check.jpg` |
| `key_green.py` | img/green/*.webp (characters on green) → img/<name>.png cut-outs + `review/green_check.jpg` (explainer-fast actors) |
| `voice.py` | script → voice.wav + words.json (`--sentence-gap` = calm pause between sentences) |
| `match_images.py` | incoming/ → img/ by prompt name |
| `check_plan.py` | refuse broken plans / unsourced numbers before render |
| `render.sh` | Remotion render (Node 22) → out/raw.mp4 |
| `finish.py` | −14 LUFS + length + black-frame checks → out/final.mp4 |
| `contact_sheet.py` | review sheets (one frame per shot) |
| `facts_review.py` | facts table for the owner's manual check |
| `make_sfx.py` | generated SFX (whooshes, impacts, sparkle…) + Kokoro crowd reactions; skips files that exist |

Recorded SFX (`library/sfx/*_r*.wav`, Mixkit free licence + CC0) are listed in `library/sfx.json` and `library/sfx_incoming/review.md`. The explainer-fast renderer plays them through pools in `remotion/src/styles/explainer-fast/sounds.json`. The Mixkit licence forbids sharing the files on their own: keep `*.wav` out of git (already in `.gitignore`).

## Tests
`engine/.venv/bin/python -m unittest discover -s engine/tests` (no network needed).

## Renderer (`engine/remotion/src/`)
`Root.tsx` registers one composition per style. `common/` = shared parts (timing, captions, audio). `styles/<style>/` = what's unique to a style. A render reads one run folder (render.sh stages it as Remotion's public dir).
