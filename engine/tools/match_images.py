"""Move generated images from a run's incoming/ into img/, named after image_prompts.txt.

Usage: engine/.venv/bin/python engine/tools/match_images.py runs/<niche>/<id>
image_prompts.txt has one prompt per line: "<name>: <prompt>" or "<name> | <prompt>",
e.g. "01_office: Skulsy at a desk, 1990s ...". Lines starting with # are skipped.

Matching, in this order:
1. By file name (the safe way): engine/tools/meta_save.js saves each image as "<prefix>_<name>.<ext>",
   so a file whose name ends in "_<name>" (or is exactly "<name>") gets that name. Two files for the same
   name (e.g. "x_s_vault.webp" and "x_s_vault (1).webp") is an error: you pick which one, nothing is moved for it.
2. Files with no prompt name in them fill the names still missing, oldest first (old manual flow), with a warning.
Duplicates (same bytes) are reported and skipped. g_* names (green-screen actors) go to img/green/ for key_green.py.
Nothing is overwritten and nothing is deleted: matched files are moved, leftovers stay in incoming/.
"""
import hashlib
import re
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
COPY_MARK = re.compile(r" \(\d+\)$")  # the browser's "name (1).webp" for a second download


def read_names(path):
    """Prompt names from image_prompts.txt, in order. Raises ValueError on a bad line."""
    names = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"\s*([A-Za-z0-9_\-]+)\s*[:|]", line)
        if not m:
            raise ValueError(f"bad prompt line (need '<name>: <prompt>' or '<name> | <prompt>'): {line[:60]}")
        names.append(m.group(1))
    if len(set(names)) != len(names):
        raise ValueError("the same name is used twice in image_prompts.txt")
    return names


def name_of(path, names):
    """The prompt name in this file's name (longest match wins: 's_vault_door' before 'door'), or None."""
    stem = COPY_MARK.sub("", path.stem)
    hits = [n for n in names if stem == n or stem.endswith("_" + n)]
    return max(hits, key=len) if hits else None


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    run = Path(argv[0])
    try:
        names = read_names(run / "image_prompts.txt")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    files = sorted((p for p in (run / "incoming").iterdir() if p.suffix.lower() in IMAGE_EXT), key=lambda p: p.stat().st_mtime)
    seen, unique = {}, []
    for p in files:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen:
            print(f"duplicate: {p.name} is the same image as {seen[h]} (skipped; Meta AI sometimes re-sends the old image)")
            continue
        seen[h] = p.name
        unique.append(p)

    by_name, unnamed = {}, []
    for p in unique:
        n = name_of(p, names)
        (by_name.setdefault(n, []) if n else unnamed).append(p)
    plan, problems = {}, 0
    for n, ps in by_name.items():
        if len(ps) > 1:
            print(f"ERROR: {len(ps)} different images for {n}: {', '.join(p.name for p in ps)}; "
                  "keep the right one in incoming/, move the other out, then run again", file=sys.stderr)
            problems += 1
        else:
            plan[n] = ps[0]
    # names already in img/ (an earlier run of this tool) are done, so a second run only fills the gaps
    done = {q.stem for d in (run / "img", run / "img" / "green") if d.exists() for q in d.iterdir()
            if q.suffix.lower() in IMAGE_EXT}
    missing = [n for n in names if n not in plan and n not in by_name and n not in done]
    if unnamed and missing:
        print(f"warning: {len(unnamed)} file(s) without a prompt name; matched by time order, check the contact sheet")
    for n, p in zip(missing, unnamed):
        plan[n] = p

    (run / "img").mkdir(exist_ok=True)
    for n in names:
        if n not in plan:
            continue
        p = plan[n]
        folder = run / "img" / "green" if n.startswith("g_") else run / "img"
        folder.mkdir(exist_ok=True)
        dst = folder / f"{n}{p.suffix.lower()}"
        if dst.exists():
            print(f"skip: {dst.relative_to(run)} already exists (not overwritten)")
            continue
        p.rename(dst)
        print(f"{p.name} -> {dst.relative_to(run)}")
    still = [n for n in names if n not in plan and n not in done]
    if still:
        print(f"MISSING: {len(still)} image(s): " + ", ".join(still), file=sys.stderr)
    left = len(unique) - len(plan)
    if left > 0:
        print(f"note: {left} file(s) left in incoming/")
    return 1 if still or problems else 0


if __name__ == "__main__":
    sys.exit(main())
