"""Check a run before rendering. Prints every problem; exit code 1 if any ERROR.

Usage: engine/.venv/bin/python engine/tools/check_plan.py runs/<id> [--test]
  --test: skip the 2:00-2:48 total length rule (short test clips)

What it checks (see .claude/skills/video-core/references/plan-schema.md):
  numbers   every number in script.txt and in on-screen text matches a facts.json entry (years excepted);
            amounts are written as digits ("$41,100", not "forty one thousand")
  wording   no banned hype / advice phrases
  plan      known style, only known fields, word indexes in range and increasing, shot lengths in limits
  files     images, SFX, music, data files exist; chart dates inside the data; chart shots have a `teach` line
  sync      words.json matches script.txt (voice is not stale); total length
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_LEN, MAX_LEN = 120.0, 168.0
LAST_SHOT_MAX = 4.0

# Per style: allowed shot fields, required ones, shot length limits in seconds (hard min/max).
STYLES = {
    "vintage-story": {
        "plan_fields": {"version", "style", "data", "beds", "music", "endCard", "tailSeconds", "shots", "charts", "notes"},
        "shot_fields": {"from", "type", "sfx", "img", "motion", "zoom", "focus", "grade", "stamp", "flash", "shake",
                        "sticker", "chart", "to", "color", "cues", "teach"},
        "types": {"image": {"img"}, "chart": {"chart", "to", "teach"}},
        "motions": {"pushIn", "pullOut", "panL", "panR", "panUp", "panDown", None},
        "shot_len": (0.5, 7.0),  # reference reel: typical 1.5-3 s, montage bursts 0.3-0.5 s
    },
    "flat-fastcut": {
        "plan_fields": {"version", "style", "data", "beds", "music", "endCard", "tailSeconds", "shots", "notes"},
        "shot_fields": {"from", "bg", "sfx", "shake", "speedLines", "push", "layers", "teach"},
        "types": None,
        "layer_types": {"skulsy", "phone", "arrow", "money", "sign", "grandma"},
        "caption_band": (760, 930),  # caption centre at 44% of 1920 px, ~118 px font
        "shot_len": (0.25, 2.5),  # reference reel: average 0.95 s; under ~8 frames can't be seen
    },
}

BANNED = ["guaranteed", "risk-free", "risk free", "can't lose", "cannot lose", "get rich quick", "buy now",
          "you should buy", "you should sell", "will go up", "will go to the moon", "sure thing", "financial freedom in",
          "100x", "1000x", "not a scam", "secret method"]
NUMBER_WORDS = re.compile(r"\b(hundred|thousand|million|billion|trillion|percent)\b", re.I)
NUM = re.compile(r"(?<![\w.-])(\$?)(\d[\d,]*(?:\.\d+)?)\s?([kKmMbB](?![a-zA-Z])|%|x(?![a-zA-Z])|times\b)?")


def parse_numbers(text):
    """'$41,100' -> ('$', 41100.0); '66%' -> ('%', 66); '$262K' -> ('$', 262000); years 1900-2099 skipped."""
    out = []
    for m in NUM.finditer(text):
        dollar, digits, suffix = m.group(1), m.group(2).replace(",", ""), (m.group(3) or "").strip().lower()
        try:
            v = float(digits)
        except ValueError:
            continue
        if not dollar and not suffix and re.fullmatch(r"(19|20)\d\d", digits):
            continue  # a year
        v *= {"k": 1e3, "m": 1e6, "b": 1e9}.get(suffix, 1)
        unit = "$" if dollar else "%" if suffix == "%" else "x" if suffix in ("x", "times") else ""
        out.append((m.group(0).strip(), unit, v))
    return out


def fact_numbers(facts):
    vals = []
    for f in facts:
        texts = [f.get("say", "")] + list((f.get("also") or {}).values())
        for t in texts:
            vals += [(u, v) for _, u, v in parse_numbers(str(t))]
    return vals


def matches(unit, v, known):
    return any((u == unit or not unit or not u) and abs(v - kv) <= 0.005 * max(abs(kv), 1) for u, kv in known)


def check(run, test=False):
    errors, warnings = [], []
    E, W = errors.append, warnings.append

    def load(name, required=True):
        p = run / name
        if not p.exists():
            if required:
                E(f"{name} missing")
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError as e:
            E(f"{name} is not valid JSON: {e}")
            return None

    plan, words_file = load("plan.json"), load("words.json")
    facts = load("facts.json") or []
    script = (run / "script.txt").read_text() if (run / "script.txt").exists() else ""
    if not script.strip():
        E("script.txt missing or empty")
    if plan is None or words_file is None:
        return errors, warnings
    words = words_file["words"]

    # --- sync: words.json made from this script? ---
    if [w["word"] for w in words] != script.split():
        E("words.json doesn't match script.txt: script changed after voice.py. Re-run voice.py")

    # --- wording ---
    low = script.lower()
    for b in BANNED:
        if b in low:
            E(f'banned phrase in script: "{b}"')
    for m in NUMBER_WORDS.finditer(script):
        E(f'write amounts as digits ("$41,100", "66%"), found "{m.group(0)}" near "{script[max(0, m.start() - 25):m.end() + 5]}"')

    # --- numbers must come from facts.json ---
    if not isinstance(facts, list):
        E("facts.json must be a list of facts")
        facts = []
    known = fact_numbers(facts)
    for f in facts:
        if f.get("kind") != "illustrative" and not f.get("source"):
            E(f"fact {f.get('id')} has no source (or mark it \"kind\": \"illustrative\" for story-only numbers)")
        if "manual" in str(f.get("check", "")).lower():
            W(f"fact {f.get('id')} needs a manual check before upload")
    on_screen = []
    for s in plan.get("shots", []):
        for k in ("stamp",):
            if s.get(k):
                on_screen.append(s[k])
        if s.get("sticker"):
            on_screen.append(s["sticker"].get("text", ""))
        for l in s.get("layers", []):
            on_screen += (l.get("props") or {}).get("lines", [])
    for c in (plan.get("charts") or {}).values():
        on_screen += [c.get("title", ""), c.get("subtitle", "")]
    for where, text in [("script", script)] + [("on screen", t) for t in on_screen]:
        for raw, unit, v in parse_numbers(text):
            if not matches(unit, v, known):
                E(f'{where}: "{raw}" is not in facts.json')

    # --- plan structure ---
    style = STYLES.get(plan.get("style"))
    if not style:
        E(f"unknown style {plan.get('style')!r} (known: {', '.join(STYLES)})")
        return errors, warnings
    if plan.get("version") != 1:
        E("plan.json version must be 1")
    for k in set(plan) - style["plan_fields"]:
        E(f"plan.json: unknown field {k!r}")
    shots = plan.get("shots") or []
    if not shots:
        E("plan has no shots")
        return errors, warnings
    if shots[0].get("from") != 0:
        E("first shot must start at word 0")

    sfx_dir, music_dir = ROOT / "library" / "sfx", ROOT / "library" / "music"
    def need_sfx(name, where):
        if not (sfx_dir / f"{name}.wav").exists():
            E(f"{where}: sfx {name!r} not in library/sfx")
    for b in plan.get("beds") or []:
        need_sfx(b.get("sfx"), "beds")
    if plan.get("music") and not (music_dir / f"{plan['music'].get('track')}.mp3").exists():
        E(f"music {plan['music'].get('track')!r} not in library/music")

    data = {}
    for name, f in (plan.get("data") or {}).items():
        d = load(f)
        if d:
            data[name] = d

    end_time = words_file["duration"] + plan.get("tailSeconds", 0.4 if plan["style"] == "vintage-story" else 0.5)
    lo, hi = style["shot_len"]
    chart_pos = {}
    prev = -1
    for i, s in enumerate(shots):
        where = f"shot {i}"
        for k in set(s) - style["shot_fields"]:
            E(f"{where}: unknown field {k!r}")
        w = s.get("from")
        if not isinstance(w, int) or not (0 <= w < len(words)):
            E(f"{where}: word index {w!r} out of range 0-{len(words) - 1}")
            continue
        if w <= prev:
            E(f"{where}: starts at word {w}, not after previous shot (word {prev})")
        prev = w
        start = 0 if i == 0 else words[w]["start"]
        nxt = shots[i + 1].get("from") if i + 1 < len(shots) else None
        end = words[nxt]["start"] if isinstance(nxt, int) and 0 <= nxt < len(words) else end_time
        length = end - start
        hi_here = max(hi, LAST_SHOT_MAX) if i == len(shots) - 1 else hi  # the closing line may hold longer
        if not (lo <= length <= hi_here):
            E(f"{where} (word {w} \"{words[w]['word']}\"): {length:.2f}s long, style allows {lo}-{hi_here}s")
        if s.get("sfx"):
            need_sfx(s["sfx"], where)
        for c in s.get("cues") or []:
            if not (0 <= c.get("word", -1) < len(words)):
                E(f"{where}: cue word {c.get('word')} out of range")
            need_sfx(c.get("sfx"), f"{where} cue")

        if style["types"] is not None:
            t = s.get("type")
            if t not in style["types"]:
                E(f"{where}: type {t!r} not one of {sorted(style['types'])}")
                continue
            for k in style["types"][t] - set(s):
                E(f"{where}: {t} shot needs {k!r}")
            if t == "image" and s.get("img") and not (run / "img" / s["img"]).exists():
                E(f"{where}: image img/{s['img']} missing")
            if s.get("motion") not in style["motions"]:
                E(f"{where}: unknown motion {s.get('motion')!r}")
            if t == "chart" and s.get("chart"):
                spec = (plan.get("charts") or {}).get(s["chart"])
                if not spec:
                    E(f"{where}: chart {s['chart']!r} not defined in plan.charts")
                    continue
                d = data.get(spec.get("data"))
                if not d:
                    E(f"{where}: chart data {spec.get('data')!r} not in plan.data")
                    continue
                first, last = d["series"][0]["date"], d["series"][-1]["date"]
                to = s.get("to", "")
                if not (spec["start"] <= to <= last) or spec["start"] < first:
                    E(f"{where}: chart dates {spec['start']}..{to} outside data {first}..{last}")
                if to <= chart_pos.get(s["chart"], ""):
                    E(f"{where}: chart {s['chart']!r} goes backwards to {to}")
                chart_pos[s["chart"]] = to
        else:
            for l in s.get("layers") or []:
                if l.get("type") not in style["layer_types"]:
                    E(f"{where}: unknown layer type {l.get('type')!r}")
                # The caption sits at 44% height (y ~845); text-like layers there get covered by it.
                cap_lo, cap_hi = style["caption_band"]
                if l.get("type") in ("sign", "phone") and l["y"] - l["h"] / 2 < cap_hi and l["y"] + l["h"] / 2 > cap_lo:
                    W(f"{where}: {l['type']} overlaps the caption band (y {cap_lo}-{cap_hi}); move it up or down")

    total = end_time + (plan.get("endCard") or {}).get("seconds", 0)
    if not test and not (MIN_LEN <= total <= MAX_LEN):
        E(f"total length {total:.1f}s outside {MIN_LEN:.0f}-{MAX_LEN:.0f}s")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    errors, warnings = check(Path(a.run), a.test)
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
