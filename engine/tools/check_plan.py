"""Check a run before rendering. Prints every problem; exit code 1 if any ERROR.

Usage: engine/.venv/bin/python engine/tools/check_plan.py runs/<niche>/<id> [--test]
  --test: skip the total length rule (short test clips)

Niche rules (length, allowed styles, banned phrases) come from the run's own niche.json,
copied in by new_run.py, so each niche's rules stay separate.

What it checks (see .claude/skills/video-core/references/plan-schema.md):
  numbers   every number in script.txt and in on-screen text matches a facts.json entry (years excepted);
            amounts are written as digits ("$41,100", not "forty one thousand")
  wording   no banned phrases (from niche.json)
  plan      known style, only known fields, word indexes in range and increasing, shot lengths in limits
  files     images, SFX, music, data files exist; chart dates inside the data; chart shots have a `teach` line
  sync      words.json matches script.txt (voice is not stale); total length
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAST_SHOT_MAX = 4.0
CLIP_MAX = 8.5

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
    "stickman-calm": {
        "plan_fields": {"version", "style", "beds", "music", "tailSeconds", "shots", "notes"},
        "shot_fields": {"from", "type", "img", "clip", "motion", "zoom", "focus", "sfx", "captionTop"},
        "types": {"image": {"img"}, "clip": {"clip"}},
        "motions": {"pushIn", "pullOut", "panL", "panR", "panUp", "panDown", None},
        "shot_len": (2.0, 7.0),  # reference reels: ~3.7-4.4 s average; calm pace, nothing flashes by
    },
    "explainer-fast": {
        "plan_fields": {"version", "style", "beds", "music", "tailSeconds", "cutSfxVolume", "mgVolume", "shots", "notes"},
        "shot_fields": {"from", "img", "bg", "cam", "zoom", "focus", "actors", "mg", "fx", "sfx", "sfxVolume", "cutSfx", "captionY", "hold"},
        "types": None,
        # must match CAMS in ExplainerFast.tsx
        "cams": {"pushIn", "pullOut", "craneDown", "craneUp", "panL", "panR", "tiltDown", "tiltUp",
                 "orbitL", "orbitR", "dive", "roll", "whip", None},
        "actor_fields": {"img", "x", "y", "h", "flip", "at", "enter", "idle"},
        "enters": {"pop", "slideL", "slideR", "drop", "none", None},
        "idles": {"breathe", "bob", "wobble", "hop", "shake", "lean", "none", None},
        "fx": {"flash", "shake", "punch"},
        # motion graphics ("mg"); must match Graphics.tsx. Value = allowed "dir" values (None = no dir).
        "mg_types": {"stamp": None, "label": None, "counter": None, "arrow": {"up", "down"},
                     "money": {"rain", "left", "right"}, "speedLines": None, "marks": None, "cross": None,
                     "circle": None, "pointer": {"left", "right", "up", "down"}},
        "mg_fields": {"type", "x", "y", "size", "at", "text", "to", "dir", "rot", "sfx"},
        "shot_len": (0.7, 4.0),  # reference reels: a new picture every ~1.5-2 s; 4 s max keeps the pace up
    },
}
# Pause after the last word when plan.json has no tailSeconds; must match each style's renderer default.
# explainer-fast sound pools ("whoosh" -> one of whoosh_r1, ...); shared with the renderer
SOUND_POOLS = json.loads((ROOT / "engine/remotion/src/styles/explainer-fast/sounds.json").read_text())["pools"]
MG_MIN = 1.0  # seconds a motion graphic must stay on screen before the cut
TAIL_DEFAULT = {"vintage-story": 0.4, "flat-fastcut": 0.5, "stickman-calm": 1.0, "explainer-fast": 0.6}

# million/billion/trillion are fine after digits ("$365 million": Kokoro reads it right, "$365M" it reads "dollars em")
NUMBER_WORDS = re.compile(r"\b(hundred|thousand|percent)\b", re.I)
NUM = re.compile(r"(?<![\w.-])(\$?)(\d[\d,]*(?:\.\d+)?)\s?(million\b|billion\b|trillion\b|[kKmMbB](?![a-zA-Z])|%|x(?![a-zA-Z])|times\b)?", re.I)


def parse_numbers(text):
    """'$41,100' -> ('$', 41100.0); '66%' -> ('%', 66); '$262K' -> ('$', 262000); '$365 million' -> ('$', 365e6);
    years 1900-2099 skipped."""
    out = []
    for m in NUM.finditer(text):
        dollar, digits, suffix = m.group(1), m.group(2).replace(",", ""), (m.group(3) or "").strip().lower()
        try:
            v = float(digits)
        except ValueError:
            continue
        if not dollar and not suffix and re.fullmatch(r"(19|20)\d\d", digits):
            continue  # a year
        v *= {"k": 1e3, "m": 1e6, "b": 1e9, "million": 1e6, "billion": 1e9, "trillion": 1e12}.get(suffix, 1)
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


def media_seconds(path):
    """Length of a video file in seconds (ffprobe), or None if missing/unreadable."""
    if not path.exists():
        return None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def load_niche(run):
    """The run's niche.json, checked. Raises ValueError with a plain message if missing or malformed."""
    p = Path(run) / "niche.json"
    if not p.exists():
        raise ValueError(f"{p} missing: runs made before niches were separated need a copy of "
                         ".claude/skills/niche-<name>/niche.json")
    try:
        n = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"{p} is not valid JSON: {e}")
    lo_hi = n.get("length_seconds")
    if not (isinstance(lo_hi, list) and len(lo_hi) == 2 and all(isinstance(x, (int, float)) for x in lo_hi)
            and 0 < lo_hi[0] < lo_hi[1]):
        raise ValueError(f"{p}: length_seconds must be [min, max] seconds")
    if not (isinstance(n.get("styles"), list) and n["styles"]):
        raise ValueError(f"{p}: styles must be a non-empty list")
    if not isinstance(n.get("banned", []), list):
        raise ValueError(f"{p}: banned must be a list")
    return n


def check_explainer_shot(s, i, where, run, words, nxt, style, E, W):
    """explainer-fast: background image, camera move, cut-out actors, effects, caption height."""
    if not s.get("img") and not s.get("bg"):
        E(f"{where}: needs 'img' (a picture) or 'bg' (a colour card)")
    elif s.get("img") and not (run / "img" / s["img"]).exists():
        E(f"{where}: image img/{s['img']} missing")
    if s.get("bg") and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(s["bg"])):
        E(f"{where}: bg must be a colour like \"#2f8f46\"")
    if s.get("cam") not in style["cams"]:
        E(f"{where}: unknown cam {s.get('cam')!r} (known: {', '.join(sorted(c for c in style['cams'] if c))})")
    for f in s.get("fx") or []:
        if f not in style["fx"]:
            E(f"{where}: unknown fx {f!r}")
    if "captionY" in s and not (0.05 <= s["captionY"] <= 0.9):
        E(f"{where}: captionY {s['captionY']} outside 0.05-0.9")
    last_word = (nxt if isinstance(nxt, int) else len(words)) - 1
    for j, a in enumerate(s.get("actors") or []):
        aw = f"{where} actor {j}"
        for k in set(a) - style["actor_fields"]:
            E(f"{aw}: unknown field {k!r}")
        for k in ("img", "x", "y", "h"):
            if k not in a:
                E(f"{aw}: needs {k!r}")
        if a.get("img") and not (run / "img" / a["img"]).exists():
            E(f"{aw}: cut-out img/{a['img']} missing (made by key_green.py from img/green/)")
        if not all(0 <= a.get(k, 0.5) <= 1.2 for k in ("x", "y")) or not (0.05 <= a.get("h", 0.5) <= 1.2):
            E(f"{aw}: x/y must be 0-1.2 and h 0.05-1.2 (shares of the frame)")
        if a.get("enter") not in style["enters"]:
            E(f"{aw}: unknown enter {a.get('enter')!r}")
        if a.get("idle") not in style["idles"]:
            E(f"{aw}: unknown idle {a.get('idle')!r}")
        if "at" in a and not (s["from"] <= a["at"] <= last_word):
            E(f"{aw}: enters at word {a['at']}, outside this shot (words {s['from']}-{last_word})")
    cap = s.get("captionY", 0.7)
    for j, g in enumerate(s.get("mg") or []):
        gw = f"{where} mg {j}"
        t = g.get("type")
        if t not in style["mg_types"]:
            E(f"{gw}: unknown type {t!r} (known: {', '.join(style['mg_types'])})")
            continue
        for k in set(g) - style["mg_fields"]:
            E(f"{gw}: unknown field {k!r}")
        if t in ("stamp", "label") and not g.get("text"):
            E(f"{gw}: {t} needs 'text'")
        if t == "counter" and not isinstance(g.get("to"), (int, float)):
            E(f"{gw}: counter needs a number 'to'")
        dirs = style["mg_types"][t]
        if "dir" in g and (dirs is None or g["dir"] not in dirs):
            E(f"{gw}: dir {g['dir']!r} not allowed for {t} (allowed: {', '.join(sorted(dirs or [])) or 'none'})")
        if not all(0 <= g.get(k, 0.5) <= 1 for k in ("x", "y")) or not (0.05 <= g.get("size", 0.5) <= 1.2):
            E(f"{gw}: x/y must be 0-1 and size 0.05-1.2 (shares of the frame)")
        if "at" in g and not (s["from"] <= g["at"] <= last_word):
            E(f"{gw}: appears at word {g['at']}, outside this shot (words {s['from']}-{last_word})")
        if g.get("sfx") and g["sfx"] not in SOUND_POOLS and not (ROOT / "library" / "sfx" / f"{g['sfx']}.wav").exists():
            E(f"{gw}: sfx {g['sfx']!r} not in library/sfx")
        # Text graphics centred near the caption get covered by it.
        if t in ("stamp", "label", "counter", "marks") and abs(g.get("y", 0.3) - cap) < 0.1:
            W(f"{gw}: {t} at y {g.get('y', 0.3)} sits on the caption (y {cap}); move it up")


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

    try:
        niche = load_niche(run)
    except ValueError as e:
        E(str(e))
        return errors, warnings
    min_len, max_len = niche["length_seconds"]
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
    for b in niche.get("banned", []):
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
        for g in s.get("mg") or []:
            on_screen.append(str(g.get("text", "")))
            if isinstance(g.get("to"), (int, float)):
                # a counter's word belongs to its number: 365 + "MILLION DOLLARS" = $365 million
                on_screen.append(f"{g['to']:,} {g.get('text', '')}")
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
    if plan["style"] not in niche["styles"]:
        E(f"style {plan['style']!r} is not used by niche {niche.get('niche')!r} (allowed: {', '.join(niche['styles'])})")
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
    pools = SOUND_POOLS if "cams" in style else {}  # only explainer-fast plays pools
    def need_sfx(name, where):
        if name not in pools and not (sfx_dir / f"{name}.wav").exists():
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

    end_time = words_file["duration"] + plan.get("tailSeconds", TAIL_DEFAULT[plan["style"]])
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
        # hold (explainer-fast): the cut comes that many seconds after its word
        start = 0 if i == 0 else words[w]["start"] + s.get("hold", 0)
        nxt = shots[i + 1].get("from") if i + 1 < len(shots) else None
        end = (words[nxt]["start"] + shots[i + 1].get("hold", 0)) if isinstance(nxt, int) and 0 <= nxt < len(words) else end_time
        if not (0 <= s.get("hold", 0) <= 0.6):
            E(f"{where}: hold {s.get('hold')} outside 0-0.6 s (a longer lag makes the picture miss the words)")
        # A graphic must stay long enough to be read (owner: "scene shifted way early, could not see the graphic").
        for j, g in enumerate(s.get("mg") or []):
            at = g.get("at")
            appear = max(start, words[at]["start"]) if isinstance(at, int) and 0 <= at < len(words) else start
            if end - appear < MG_MIN:
                E(f"{where} mg {j} ({g.get('type')} {g.get('text', '')!r}): on screen only {end - appear:.2f}s, needs {MG_MIN}s; "
                  f"move 'at' earlier or give the next shot a 'hold'")
        length = end - start
        hi_here = max(hi, LAST_SHOT_MAX) if i == len(shots) - 1 else hi  # the closing line may hold longer
        if s.get("type") == "clip":
            hi_here = max(hi_here, CLIP_MAX)  # animated clips are 5-8 s; the clip-length check below is the real limit
        if not (lo <= length <= hi_here):
            E(f"{where} (word {w} \"{words[w]['word']}\"): {length:.2f}s long, style allows {lo}-{hi_here}s")
        if s.get("sfx"):
            need_sfx(s["sfx"], where)
        if s.get("cutSfx"):
            need_sfx(s["cutSfx"], where)
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
            if t == "clip" and s.get("clip"):
                clip_len = media_seconds(run / "img" / s["clip"])
                if clip_len is None:
                    E(f"{where}: clip img/{s['clip']} missing or unreadable")
                elif length > clip_len:
                    E(f"{where}: shot is {length:.2f}s but clip img/{s['clip']} is only {clip_len:.2f}s; start the next shot earlier")
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
        elif "cams" in style:
            check_explainer_shot(s, i, where, run, words, nxt, style, E, W)
        else:
            for l in s.get("layers") or []:
                if l.get("type") not in style["layer_types"]:
                    E(f"{where}: unknown layer type {l.get('type')!r}")
                # The caption sits at 44% height (y ~845); text-like layers there get covered by it.
                cap_lo, cap_hi = style["caption_band"]
                if l.get("type") in ("sign", "phone") and l["y"] - l["h"] / 2 < cap_hi and l["y"] + l["h"] / 2 > cap_lo:
                    W(f"{where}: {l['type']} overlaps the caption band (y {cap_lo}-{cap_hi}); move it up or down")

    total = end_time + (plan.get("endCard") or {}).get("seconds", 0)
    if not test and not (min_len <= total <= max_len):
        E(f"total length {total:.1f}s outside {min_len:.0f}-{max_len:.0f}s (niche {niche.get('niche')})")
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
