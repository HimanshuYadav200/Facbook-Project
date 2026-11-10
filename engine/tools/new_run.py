"""Create a new run folder with the standard layout.

Usage: engine/.venv/bin/python engine/tools/new_run.py <slug> --niche <niche> [--style <style>]
Creates runs/<niche>/<YYYY-MM-DD>_<slug>/ and prints its path. Refuses to touch an existing folder.
Copies .claude/skills/niche-<niche>/niche.json into the run, so the run keeps the rules it was made with.
The style defaults to the niche's first style.
"""
import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_plan import load_niche  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".claude" / "skills"

BRIEF = """# Brief: {slug}

- niche: {niche}
- style: {style}
- target length: {length}
- topic / angle:
- viewer promise (what they understand by the end):
- key facts to fetch (exact tickers, series, dates):
"""

LOG = """# Log: {slug}

| when | step | notes |
|---|---|---|
| {today} | created | niche {niche}, style {style} |
"""


def mmss(s):
    return f"{int(s) // 60}:{int(s) % 60:02d}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--niche", required=True, help="e.g. skulsy-finance, stickman-money")
    ap.add_argument("--style")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9-]+", a.slug):
        print("ERROR: slug must be lowercase letters, digits and dashes", file=sys.stderr)
        return 1
    src = SKILLS / f"niche-{a.niche}"
    if not (src / "niche.json").exists():
        known = sorted(p.parent.name.removeprefix("niche-") for p in SKILLS.glob("niche-*/niche.json"))
        print(f"ERROR: unknown niche {a.niche!r} (known: {', '.join(known)})", file=sys.stderr)
        return 1
    try:
        niche = load_niche(src)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    style = a.style or niche["styles"][0]
    if style not in niche["styles"]:
        print(f"ERROR: niche {a.niche} uses styles {', '.join(niche['styles'])}, not {style!r}", file=sys.stderr)
        return 1
    today = date.today().isoformat()
    run = ROOT / "runs" / a.niche / f"{today}_{a.slug}"
    if run.exists():
        print(f"ERROR: {run} already exists", file=sys.stderr)
        return 1
    for d in ("data", "img", "incoming", "review", "out"):
        (run / d).mkdir(parents=True)
    shutil.copy2(src / "niche.json", run / "niche.json")
    lo, hi = niche["length_seconds"]
    v = dict(slug=a.slug, niche=a.niche, style=style, today=today, length=f"{mmss(lo)}-{mmss(hi)}")
    (run / "brief.md").write_text(BRIEF.format(**v))
    (run / "log.md").write_text(LOG.format(**v))
    (run / "facts.json").write_text("[]\n")
    (run / "script.txt").write_text("")
    print(run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
