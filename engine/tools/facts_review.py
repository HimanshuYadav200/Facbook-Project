"""Write review/facts_review.md: every number in the video with its source, for the owner to tick before upload.

Usage: engine/.venv/bin/python engine/tools/facts_review.py runs/<niche>/<id>
Manual-check facts come first, then data facts, then illustrative (story-only) numbers.
"""
import json
import sys
from pathlib import Path


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    run = Path(argv[0])
    facts = json.loads((run / "facts.json").read_text())

    def order(f):
        if "manual" in str(f.get("check", "")).lower():
            return 0
        return 2 if f.get("kind") == "illustrative" else 1

    rows = ["# Facts review: " + run.name, "",
            "Tick each line after opening the source. Manual-check items first.", "",
            "| ✓ | id | says | what | period | source | cross-check | data file |", "|---|---|---|---|---|---|---|---|"]
    for f in sorted(facts, key=order):
        period = " → ".join(f.get("period", [])) if isinstance(f.get("period"), list) else f.get("period", "")
        src = "illustrative (story only)" if f.get("kind") == "illustrative" else f.get("source", "**MISSING**")
        cells = ["[ ]", f.get("id", ""), f.get("say", ""), f.get("what", ""), period, src, f.get("check", ""), f.get("data_file", "")]
        rows.append("| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |")
    (run / "review").mkdir(exist_ok=True)
    out = run / "review" / "facts_review.md"
    out.write_text("\n".join(rows) + "\n")
    print(f"{len(facts)} facts -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
