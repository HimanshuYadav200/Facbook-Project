"""Move generated images from a run's incoming/ into img/, named after image_prompts.txt.

Usage: engine/.venv/bin/python engine/tools/match_images.py runs/<niche>/<id>
image_prompts.txt has one prompt per line: "<name>: <prompt>", e.g. "01_office: Skulsy at a desk, 1990s ..."
Files in incoming/ are taken oldest first (the order they were generated/downloaded) and get those names,
keeping their extension: img/01_office.webp. Duplicates (same bytes) are reported and skipped.
Nothing is overwritten and nothing is deleted: matched files are moved, leftovers stay in incoming/.
"""
import hashlib
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    run = Path(argv[0])
    names = []
    for line in (run / "image_prompts.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name = line.split(":", 1)[0].strip()
            if not name or " " in name:
                print(f"ERROR: bad prompt line (need '<name>: <prompt>'): {line[:60]}", file=sys.stderr)
                return 1
            names.append(name)
    files = sorted((p for p in (run / "incoming").iterdir() if p.suffix.lower() in IMAGE_EXT), key=lambda p: p.stat().st_mtime)
    seen, unique = {}, []
    for p in files:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            print(f"duplicate: {p.name} is the same image as {seen[h]} (skipped; Meta AI sometimes re-sends the old image)")
            continue
        seen[h] = p.name
        unique.append(p)
    (run / "img").mkdir(exist_ok=True)
    for name, p in zip(names, unique):
        dst = run / "img" / f"{name}{p.suffix.lower()}"
        if dst.exists():
            print(f"skip: {dst.name} already exists (not overwritten)")
            continue
        p.rename(dst)
        print(f"{p.name} -> img/{dst.name}")
    if len(unique) < len(names):
        print(f"MISSING: {len(names) - len(unique)} image(s): " + ", ".join(names[len(unique):]), file=sys.stderr)
        return 1
    if len(unique) > len(names):
        print(f"note: {len(unique) - len(names)} extra file(s) left in incoming/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
