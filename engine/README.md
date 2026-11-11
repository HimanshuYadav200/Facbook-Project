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
| `find_eyes.py` | images → `eyes.json` (stickman eye positions for blinking; also heads under hair and round glasses) + `review/eyes_check.jpg` |
| `key_green.py` | img/green/*.webp (characters on green) → img/<name>.png cut-outs + `review/green_check.jpg` (explainer-fast actors) |
| `voice.py` | script → voice.wav + words.json (`--sentence-gap` = calm pause between sentences) |
| `meta_save.js` | pasted into the meta.ai tab: saves only new images (never lazy-loaded old ones), named `<tag>_<prompt name>.<real type>` |
| `match_images.py` | incoming/ → img/ by prompt name in the file name (`name: prompt` or `name \| prompt` lines; `g_*` → img/green/; two files for one name = error) |
| `check_plan.py` | refuse broken plans / unsourced numbers before render |
| `render.sh` | Remotion render (Node 22) → out/raw.mp4 |
| `finish.py` | −14 LUFS + length + true peak (≤ −1 dB) + black-frame checks → out/final.mp4 |
| `contact_sheet.py` | review sheets (one frame per shot) |
| `fact_check.py` | Tavily + Exa web search per fact → `review/fact_check.md` (CONFIRMED on 2+ sites / ONE SITE / NOT FOUND); `--apply` clears manual marks of confirmed facts (backup first). `TAVILY_API_KEY` (+ `_BACKUP`) and `EXA_API_KEY` in .env; one engine failing doesn't stop the other |
| `facts_review.py` | facts table for the owner's manual check |
| `make_sfx.py` | generated SFX (whooshes, impacts, sparkle…) + Kokoro crowd reactions; skips files that exist |
| `gen_sfx.py` | text prompt → custom SFX with the local Stable Audio 3 Small SFX model → `library/sfx/<name>.wav` + licence entry in `sfx.json` (never overwrites) |

Recorded SFX (`library/sfx/*_r*.wav`, Mixkit free licence + CC0) and generated ones (`gen_*`, Stable Audio 3) are listed in `library/sfx.json` and `library/sfx_incoming/review.md` + `review_2026-11-11.md`. The explainer-fast renderer plays them through pools in `remotion/src/styles/explainer-fast/sounds.json`. The Mixkit licence forbids sharing the files on their own: keep `*.wav` out of git (already in `.gitignore`).

### Local SFX model (Stable Audio 3 Small SFX), outside the project
Kept in its own venv so its packages never touch `engine/.venv`. Set up once (done 2026-11-11):
```zsh
/opt/homebrew/bin/python3.12 -m venv ~/tools/stable-audio-3
git clone --depth=1 https://github.com/Stability-AI/stable-audio-3 ~/tools/stable-audio-3/sa3-repo
~/tools/stable-audio-3/bin/pip install -r ~/tools/stable-audio-3/sa3-repo/optimized/mlx/requirements.txt
cd ~/tools/stable-audio-3/sa3-repo/optimized/mlx && ~/tools/stable-audio-3/bin/python scripts/install.py --download sm-sfx
```
Weights (~1.3 GB) sit in the Hugging Face cache (`~/.cache/huggingface/hub`); `gen_sfx.py` runs the model offline. We do **not** run Stability's `bootstrap.sh`/`install.sh` (they install `uv` and edit the shell profile). Speed on the M5: ~1 s of sound per second, ~1.5 GB RAM. Licence: Stability AI Community License (free commercial use under $1M yearly revenue **after registering with Stability AI**) plus Gemma terms for the text encoder.

## Tests
`engine/.venv/bin/python -m unittest discover -s engine/tests` (no network needed).

## Renderer (`engine/remotion/src/`)
`Root.tsx` registers one composition per style. `common/` = shared parts (timing, captions, audio). `styles/<style>/` = what's unique to a style. A render reads one run folder (render.sh stages it as Remotion's public dir).
