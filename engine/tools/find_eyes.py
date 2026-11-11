"""Find the stickmen's eyes in a run's images so the renderer can make them blink.

Usage: engine/.venv/bin/python engine/tools/find_eyes.py runs/<niche>/<id>
Writes eyes.json: {"<image file>": [{"eyes": [[x, y], [x, y]], "r": r, "tone": t}, ...]}
  x, y, r are shares of the image width/height (0-1); tone = head grey (0-255) used to paint the eye shut.
Images where no face is found get an empty list: those shots simply don't blink.
Also writes review/eyes_check.jpg: every image with a red mark on each eye found (check it once).

How: a stickman head is a big, round, near-white blob; its eyes are two small dark dots side by side
in its upper part. Round glasses are found too (two alike white lenses side by side, one dot each).
Works for the stickman-calm look only (round blank heads, dot eyes).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

W, H = 576, 1024  # analysis size (half of Meta's 1152x2048); positions are returned as shares, so size doesn't matter


def load_gray(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H}", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W).astype(float)


def find_faces(g):
    """Return [{"eyes": [[x,y],[x,y]], "r": r, "tone": t}] in shares of the image size."""
    white = nd.binary_opening(g > 225, iterations=2)
    lab, n = nd.label(white)
    faces = []
    for i in range(1, n + 1):
        m = lab == i
        area = int(m.sum())
        if area < 1200:
            continue
        ys, xs = np.nonzero(m)
        h, w = np.ptp(ys) + 1, np.ptp(xs) + 1
        # hair over the head or an ear cuts into the blob, so measure roundness with its holes filled
        if not (0.7 < h / w < 1.35 and nd.binary_fill_holes(m).sum() / (h * w) > 0.55):
            continue  # not round enough to be a head
        holes, k = nd.label(nd.binary_fill_holes(m) & ~m & (g < 90))
        if k < 2:
            continue
        idx = range(1, k + 1)
        sizes = nd.sum(holes > 0, holes, idx)
        centres = nd.center_of_mass(holes > 0, holes, idx)
        # Eyes are solid dots; eyebrows, lids and closed "^" eyes are thin strokes that fill little of their box.
        dots = []
        for (cy, cx), s, b in zip(centres, sizes, nd.find_objects(holes)):
            bh, bw = b[0].stop - b[0].start, b[1].stop - b[1].start
            solid = s / (bh * bw)
            if 4 < s < area * 0.02 and cy < ys.min() + 0.7 * h and max(bh, bw) <= 3 * min(bh, bw) and solid >= 0.4:
                dots.append((cy, cx, s))
        # Eyes = the pair of dots most alike in height, a sensible distance apart (brows and mouths are lines, not dots).
        best = None
        for a in range(len(dots)):
            for b in range(a + 1, len(dots)):
                (y1, x1, s1), (y2, x2, s2) = dots[a], dots[b]
                dx, dy = abs(x1 - x2), abs(y1 - y2)
                if 0.1 * w < dx < 0.6 * w and dy < 0.35 * dx and max(s1, s2) < 3 * min(s1, s2):
                    if best is None or dy < best[0]:
                        best = (dy, dots[a], dots[b])
        if not best:
            continue
        _, e1, e2 = best
        r = float(np.sqrt(max(e1[2], e2[2]) / np.pi))
        faces.append({"eyes": [[round(e1[1] / W, 4), round(e1[0] / H, 4)], [round(e2[1] / W, 4), round(e2[0] / H, 4)]],
                      "r": round(r / W, 4), "tone": int(np.median(g[m]))})
    return faces + find_glasses(g, lab, n, faces)


def find_glasses(g, lab, n, faces):
    """Faces with round glasses: each lens is its own small white disc with one dark eye dot inside,
    so the head test above never sees both eyes. A face = two alike lenses side by side, one solid dot each."""
    lenses = []
    for i, b in enumerate(nd.find_objects(lab), start=1):
        bh, bw = b[0].stop - b[0].start, b[1].stop - b[1].start
        if not (6 <= bw <= 90 and 0.75 < bh / bw < 1.35):
            continue
        m = lab[b] == i
        filled = nd.binary_fill_holes(m)
        if filled.sum() < 0.6 * bh * bw:
            continue  # not a disc
        dots, k = nd.label(filled & ~m & (g[b] < 90))
        if k != 1:
            continue  # a lens holds exactly one eye
        s = int((dots > 0).sum())
        if not 3 <= s <= 0.35 * filled.sum():
            continue
        cy, cx = nd.center_of_mass(dots > 0)
        lenses.append((b[0].start + cy, b[1].start + cx, bw, s, int(np.median(g[b][m]))))
    taken = {tuple(map(tuple, f["eyes"])) for f in faces}
    out, used = [], set()
    for a in range(len(lenses)):
        for c in range(a + 1, len(lenses)):
            (y1, x1, w1, s1, t1), (y2, x2, w2, s2, _) = lenses[a], lenses[c]
            dx, dy = abs(x1 - x2), abs(y1 - y2)
            if a in used or c in used or not (max(w1, w2) < 1.4 * min(w1, w2) and 1.0 * w1 < dx < 2.6 * w1
                                              and dy < 0.25 * dx and max(s1, s2) < 3 * min(s1, s2)):
                continue
            eyes = [[round(x1 / W, 4), round(y1 / H, 4)], [round(x2 / W, 4), round(y2 / H, 4)]]
            if tuple(map(tuple, eyes)) in taken:
                continue
            used |= {a, c}
            out.append({"eyes": eyes, "r": round(float(np.sqrt(max(s1, s2) / np.pi)) / W, 4), "tone": t1})
    return out


def check_sheet(run, results):
    """review/eyes_check.jpg: each image small, a red box on each eye found."""
    out = run / "review" / "eyes_check.jpg"
    out.parent.mkdir(exist_ok=True)
    tiles = []
    for name, faces in results.items():
        boxes = ",".join(f"drawbox=x={x * 288 - 6}:y={y * 512 - 6}:w=12:h=12:color=red:t=3"
                         for f in faces for x, y in f["eyes"]) or "null"
        tiles.append((name, boxes))
    inputs, chains = [], []
    for i, (name, boxes) in enumerate(tiles):
        inputs += ["-i", str(run / "img" / name)]
        chains.append(f"[{i}:v]scale=288:512,{boxes}[t{i}]")
    cols = 8
    rows = -(-len(tiles) // cols)
    layout = "|".join(f"{(i % cols) * 288}_{(i // cols) * 512}" for i in range(len(tiles)))
    graph = ";".join(chains) + ";" + "".join(f"[t{i}]" for i in range(len(tiles))) + \
        f"xstack=inputs={len(tiles)}:layout={layout}:fill=white" if len(tiles) > 1 else chains[0].replace("[t0]", "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-frames:v", "1", str(out)], check=True)
    return out, rows


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    run = Path(argv[0])
    images = sorted(p for p in (run / "img").iterdir() if p.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg"})
    if not images:
        print(f"ERROR: no images in {run / 'img'}", file=sys.stderr)
        return 1
    results = {}
    for p in images:
        results[p.name] = find_faces(load_gray(p))
        print(f"{p.name}: {len(results[p.name])} face(s)")
    (run / "eyes.json").write_text(json.dumps(results, indent=1) + "\n")
    sheet, _ = check_sheet(run, results)
    print(f"-> {run / 'eyes.json'}; check the red marks in {sheet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
