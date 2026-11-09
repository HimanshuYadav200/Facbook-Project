# Known errors and fixes

| Symptom | Cause | Fix |
|---|---|---|
| Render stuck at "Waiting for root component to load" | (a) Node 26 in use; (b) Claude Code's sandbox blocks the local server Remotion's headless Chrome talks to | (a) render.sh forces Node 22; (b) run render.sh outside the sandbox (owner has allowed this; otherwise the owner types `! engine/tools/render.sh runs/<id>`) |
| Caption shows a misspelled name | captions come from script.txt | fix spelling in script.txt, re-run voice.py |
| voice.py warns "only N% heard as written" | Kokoro misread a word/number, or Whisper mis-heard | listen to voice.wav around the odd word; rewrite it ("A I" not "AI", "262 times" not "262x") |
| Caption word "Skulsy" heard as "Skulce" | Whisper | harmless: captions use the script's spelling |
| `check_plan`: "words.json doesn't match script.txt" | script edited after voice | re-run voice.py, then re-check plan word indexes |
| `check_plan`: shot too short on fast words | Whisper timing on quick one-word lines | merge the shot into a neighbour |
| `fetch_data`: "Alpha Vantage refused" | free tier ≈ 25 requests/day, 1/s | wait; results are cached for a day (`engine/cache/`) |
| `fetch_data`: "TIINGO_API_KEY is not set" | key missing | add to `.env`, or use `--source av-weekly --check none` (weekly precision) |
| `fetch_data`: "sources disagree" | providers differ (missed split, bad data) | stop; show the owner the dates; don't use the data |
| Meta AI skips a prompt | sent too fast | wait ~30 s between prompts, one chat per video |
| Meta AI re-sends the previous image | follow-up became an "edit" | match_images.py reports duplicates (md5); regenerate that one |
| Kokoro reads a British voice oddly | lang code | voice.py takes the language from the voice name (bm_ → British) |
| Meta AI image contains invented numbers/text (tickers, headlines with %) | image models make up text | crop it out with `zoom` + `focus` (vintage), or regenerate without text; re-check on the contact sheet |
