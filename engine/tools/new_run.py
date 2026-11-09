"""Create a new run folder with the standard layout.

Usage: engine/.venv/bin/python engine/tools/new_run.py <slug> [--niche skulsy-finance] [--style vintage-story]
Creates runs/<YYYY-MM-DD>_<slug>/ and prints its path. Refuses to touch an existing folder.
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BRIEF = """# Brief: {slug}

- niche: {niche}
- style: {style}
- target length: 2:00-2:48
- topic / angle:
- viewer promise (what they understand by the end):
- key facts to fetch (exact tickers, series, dates):
"""

LOG = """# Log: {slug}

| when | step | notes |
|---|---|---|
| {today} | created | niche {niche}, style {style} |
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--niche", default="skulsy-finance")
    ap.add_argument("--style", default="vintage-story")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9-]+", a.slug):
        print("ERROR: slug must be lowercase letters, digits and dashes", file=sys.stderr)
        return 1
    today = date.today().isoformat()
    run = ROOT / "runs" / f"{today}_{a.slug}"
    if run.exists():
        print(f"ERROR: {run} already exists", file=sys.stderr)
        return 1
    for d in ("data", "img", "incoming", "review", "out"):
        (run / d).mkdir(parents=True)
    v = dict(slug=a.slug, niche=a.niche, style=a.style, today=today)
    (run / "brief.md").write_text(BRIEF.format(**v))
    (run / "log.md").write_text(LOG.format(**v))
    (run / "facts.json").write_text("[]\n")
    (run / "script.txt").write_text("")
    print(run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
