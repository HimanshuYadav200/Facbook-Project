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
| `new_run.py` | create `runs/<date>_<slug>/` |
| `fetch_data.py` | official data → `data/*.json` (Tiingo, Alpha Vantage, FRED, SEC) |
| `finance_calc.py` | numbers for facts.json (invest, change, drawdown, cagr, inflate) |
| `voice.py` | script → voice.wav + words.json |
| `match_images.py` | incoming/ → img/ by prompt name |
| `check_plan.py` | refuse broken plans / unsourced numbers before render |
| `render.sh` | Remotion render (Node 22) → out/raw.mp4 |
| `finish.py` | −14 LUFS + length + black-frame checks → out/final.mp4 |
| `contact_sheet.py` | review sheets (one frame per shot) |
| `facts_review.py` | facts table for the owner's manual check |
| `make_sfx.py` | placeholder SFX |

## Tests
`engine/.venv/bin/python -m unittest discover -s engine/tests` (no network needed).

## Renderer (`engine/remotion/src/`)
`Root.tsx` registers one composition per style. `common/` = shared parts (timing, captions, audio). `styles/<style>/` = what's unique to a style. A render reads one run folder (render.sh stages it as Remotion's public dir).
