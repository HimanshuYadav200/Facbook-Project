# plan.json (version 1)

The contract between Claude (who writes it) and the renderer (`engine/remotion/`). `check_plan.py` validates it.

## Shared fields (all styles)

| Field | Type | Meaning |
|---|---|---|
| `version` | `1` | required |
| `style` | string | `vintage-story` or `flat-fastcut`; picks the Remotion composition |
| `data` | `{name: "data/<file>.json"}` | data files the plan uses (charts) |
| `beds` | `[{sfx, volume}]` | looping ambience under everything (e.g. `vinyl` 0.35, `room` 0.4) |
| `music` | `{track, volume}` | looping music from `library/music/<track>.mp3` (licensed only). Volume ~0.08–0.15 |
| `endCard` | `{text, seconds}` | end card after the last word |
| `tailSeconds` | number | pause after the last word before the end card (default 0.4 vintage, 0.5 flat) |
| `notes` | string | free notes for humans; ignored by the renderer |
| `shots` | list | see below |

## Shots

Every shot has:
- `from`: **word index** in `words.json` where the shot starts. First shot `0`; strictly increasing. A shot lasts until the next shot's `from` (or the end).
- `sfx` (optional): name in `library/sfx.json`, plays at the cut.
- `teach` (required on teaching shots: charts, comparisons): one sentence, "the viewer sees ___ change/relate to ___".

Style-specific fields are listed in each style skill (`style-*/SKILL.md`). Unknown fields are an error.

## Word indexes
`words.json` → `words[i] = {word, start, end}`. Find an index: `P -c "import json;w=json.load(open('runs/<id>/words.json'))['words'];print([(i,x['word']) for i,x in enumerate(w)])"`.
A shot starts 0.04 s before its word, so the cut lands just ahead of the spoken word.

## Shot length limits (seconds, checked)
| Style | min | max | last shot max |
|---|---|---|---|
| vintage-story | 0.5 | 7.0 | 7.0 |
| flat-fastcut | 0.25 | 2.5 | 4.0 |
Whisper timings are least precise on fast one-word lines ("Sold. Up. Bought."): don't give each of those its own shot unless the gap between words is ≥ 0.3 s.

## Total length
`words.duration + tailSeconds + endCard.seconds` must be 120–168 s (2:00–2:48), except `--test`.
