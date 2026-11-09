"""Contact sheets for review: one frame from the middle of every shot, 40 per sheet (8 x 5).

Usage: engine/.venv/bin/python engine/tools/contact_sheet.py runs/<id> [--video out/preview.mp4]
Writes review/sheet_1.jpg, sheet_2.jpg, ... and review/sheets.txt, which says what each tile is
(tiles are numbered left to right, top to bottom, starting at 1). This ffmpeg build can't draw text,
so the labels live in the .txt file instead of on the image.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COLS, ROWS = 8, 5
TILE_W, TILE_H = 180, 320


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--video", help="video inside the run (default out/final.mp4, else out/raw.mp4)")
    a = ap.parse_args(argv)
    run = Path(a.run)
    video = run / a.video if a.video else next((run / "out" / n for n in ("final.mp4", "raw.mp4") if (run / "out" / n).exists()), None)
    if not video or not video.exists():
        print("ERROR: no rendered video in out/", file=sys.stderr)
        return 1
    plan = json.loads((run / "plan.json").read_text())
    wf = json.loads((run / "words.json").read_text())
    words, shots = wf["words"], plan["shots"]
    end_all = wf["duration"]

    tiles, lines = [], []
    tmp = Path(tempfile.mkdtemp())
    for i, s in enumerate(shots):
        start = 0.0 if i == 0 else words[s["from"]]["start"]
        nxt = shots[i + 1]["from"] if i + 1 < len(shots) else None
        end = words[nxt]["start"] if nxt is not None else end_all
        t = (start + end) / 2
        png = tmp / f"{i:04d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={TILE_W}:{TILE_H}", str(png)], check=True)
        tiles.append(png)
        said = " ".join(w["word"] for w in words[s["from"]:nxt])
        what = s.get("type") or "flat"
        detail = s.get("img") or s.get("chart") or ",".join(l.get("type", "") for l in s.get("layers", []))
        lines.append((i, t, end - start, what, detail, said))

    review = run / "review"
    review.mkdir(exist_ok=True)
    per = COLS * ROWS
    txt = []
    for n in range(0, len(tiles), per):
        sheet = n // per + 1
        batch = tmp / f"sheet{sheet}"
        batch.mkdir()
        for k, p in enumerate(tiles[n:n + per]):
            shutil.copy(p, batch / f"{k:03d}.png")
        rows = -(-len(tiles[n:n + per]) // COLS)
        out = review / f"sheet_{sheet}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(batch / "%03d.png"),
                        "-vf", f"tile={COLS}x{rows}:padding=4:color=white", "-frames:v", "1", "-q:v", "3", str(out)], check=True)
        txt.append(f"== {out.name} ==")
        for k, (i, t, ln, what, detail, said) in enumerate(lines[n:n + per]):
            txt.append(f"tile {k + 1:2d} | shot {i:3d} | {t:6.1f}s | {ln:4.1f}s long | {what}:{detail} | \"{said}\"")
    (review / "sheets.txt").write_text("\n".join(txt) + "\n")
    shutil.rmtree(tmp)
    print(f"{len(tiles)} shots -> {-(-len(tiles) // per)} sheet(s) in {review}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
