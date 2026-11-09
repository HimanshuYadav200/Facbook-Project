"""Finish a render: loudness to -14 LUFS (two-pass), then check length and black frames.

Usage: engine/.venv/bin/python engine/tools/finish.py runs/<id> [--test]
  reads out/raw.mp4, writes out/final.mp4. --test skips the 2:00-2:48 length rule (short test clips).

Two-pass: pass 1 measures the audio, pass 2 applies one fixed gain. The test version used one pass,
which adjusts volume on the fly and can make it "pump".
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.5, 11.0
MIN_LEN, MAX_LEN = 120.0, 168.0  # 2:00-2:48 (owner's rule; under YouTube Shorts' 3-min cap)


def ffmpeg(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True)


def measure(path):
    r = ffmpeg(["-i", str(path), "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
                "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise RuntimeError(f"could not measure loudness:\n{r.stderr[-500:]}")
    return json.loads(m.group(0))


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def black_frames(path):
    r = ffmpeg(["-i", str(path), "-vf", "blackdetect=d=0.3:pic_th=0.98", "-an", "-f", "null", "-"])
    return re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    run = Path(a.run)
    raw, final = run / "out" / "raw.mp4", run / "out" / "final.mp4"
    if not raw.exists():
        print(f"ERROR: {raw} missing (run render.sh first)", file=sys.stderr)
        return 1

    m = measure(raw)
    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:linear=true:"
          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    r = ffmpeg(["-y", "-i", str(raw), "-af", af, "-ar", "48000", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(final)])  # index at the start: plays/uploads everywhere
    if r.returncode != 0:
        print(f"ERROR: ffmpeg failed:\n{r.stderr[-500:]}", file=sys.stderr)
        return 1

    problems = []
    out = measure(final)
    lufs = float(out["input_i"])
    if abs(lufs - TARGET_I) > 1.0:
        problems.append(f"loudness {lufs:.1f} LUFS (target {TARGET_I})")
    length = duration(final)
    if not a.test and not (MIN_LEN <= length <= MAX_LEN):
        problems.append(f"length {length:.1f}s outside {MIN_LEN:.0f}-{MAX_LEN:.0f}s")
    blacks = [b for b in black_frames(final) if float(b[0]) < length - 3]  # an end-card fade is fine
    if blacks:
        problems.append("black frames at " + ", ".join(f"{float(s):.1f}-{float(e):.1f}s" for s, e in blacks))

    print(f"{final}: {length:.1f}s, {lufs:.1f} LUFS, true peak {float(out['input_tp']):.1f} dB")
    for p in problems:
        print(f"PROBLEM: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
