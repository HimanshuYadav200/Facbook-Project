"""Cut characters out of a green background, so the renderer can move them over a scene ("actors").

Usage: engine/.venv/bin/python engine/tools/key_green.py runs/<niche>/<id>
Reads every image in img/green/ (made on a plain bright green background), writes img/<name>.png
with a transparent background, cropped to the character. The green originals are kept.
Also writes review/green_check.jpg: every cut-out over magenta, so green left-overs and holes are easy to see.

How: a pixel is background when its green is much stronger than its red and blue ("greenness").
Edges get partial transparency, and green light spilled on the character is removed.
Characters must not wear green (the image prompt says so).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

LO, HI = 40, 110  # greenness below LO = fully kept, above HI = fully transparent, soft in between
PAD = 8  # pixels kept around the character when cropping


def load_rgb(path):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    w, h = map(int, probe.strip().split(",")[:2])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).astype(np.int16)


def save_rgba(rgba, path):
    h, w = rgba.shape[:2]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-i", "-",
                    "-frames:v", "1", str(path)], input=rgba.astype(np.uint8).tobytes(), check=True)


def key(rgb):
    """RGB image (int16) -> cropped RGBA uint8 array, or None if nothing but green is left."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    greenness = g - np.maximum(r, b)
    alpha = np.clip(1 - (greenness - LO) / (HI - LO), 0, 1)
    out = rgb.copy()
    # Despill: green tint on edges and on the character comes from the background light, cap it.
    spill = greenness > 0
    out[..., 1][spill] = np.maximum(r, b)[spill]
    ys, xs = np.nonzero(alpha > 0.5)
    if not len(ys):
        return None
    y0, y1 = max(0, ys.min() - PAD), min(rgb.shape[0], ys.max() + PAD + 1)
    x0, x1 = max(0, xs.min() - PAD), min(rgb.shape[1], xs.max() + PAD + 1)
    rgba = np.dstack([out, (alpha * 255).round()]).astype(np.uint8)
    return rgba[y0:y1, x0:x1]


def check_sheet(run, files):
    out = run / "review" / "green_check.jpg"
    out.parent.mkdir(exist_ok=True)
    inputs, chains = [], []
    for i, f in enumerate(files):
        inputs += ["-i", str(f)]
        chains.append(f"color=magenta:s=300x400[bg{i}];[{i}:v]scale=300:400:force_original_aspect_ratio=decrease[c{i}];"
                      f"[bg{i}][c{i}]overlay=(W-w)/2:(H-h)/2:shortest=1[t{i}]")
    if len(files) == 1:
        graph = chains[0].replace("[t0]", "")
    else:
        layout = "|".join(f"{(i % 6) * 300}_{(i // 6) * 400}" for i in range(len(files)))
        graph = ";".join(chains) + ";" + "".join(f"[t{i}]" for i in range(len(files))) + \
            f"xstack=inputs={len(files)}:layout={layout}:fill=white"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-frames:v", "1", str(out)], check=True)
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    run = Path(argv[0])
    src = run / "img" / "green"
    files = sorted(p for p in src.glob("*") if p.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg"}) if src.exists() else []
    if not files:
        print(f"ERROR: no images in {src}", file=sys.stderr)
        return 1
    made = []
    for p in files:
        rgba = key(load_rgb(p))
        if rgba is None:
            print(f"WARNING: {p.name}: nothing left after removing green (no character?)", file=sys.stderr)
            continue
        dst = run / "img" / f"{p.stem}.png"
        save_rgba(rgba, dst)
        made.append(dst)
        kept = (rgba[..., 3] > 127).mean()
        print(f"{p.name} -> img/{dst.name} ({rgba.shape[1]}x{rgba.shape[0]}, {kept:.0%} of the crop is character)")
    if made:
        print(f"-> check {check_sheet(run, made)}: no green fringe, no holes in the characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
