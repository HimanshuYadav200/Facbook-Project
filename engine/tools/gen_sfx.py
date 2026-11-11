"""Make a custom sound effect from a text prompt with the local Stable Audio 3 Small SFX model.

Usage: engine/.venv/bin/python engine/tools/gen_sfx.py <name> "<prompt>" [--seconds 2] [--seed N]
           [--steps N] [--cfg 1.0] [--negative "music, speech"] [--maxlen 2.5] [--tags a,b] [--mood dark]
Example: ... gen_sfx.py vault_slam "heavy steel bank vault door slams shut, deep metallic boom" --seconds 3

Writes library/sfx/<name>.wav (mono 44.1 kHz, silence trimmed, capped at --maxlen, short fade, peak -1 dBFS,
the same treatment as the downloaded pack) and adds a licence entry to library/sfx.json (backed up first).
Never overwrites an existing sound. Plans then use it like any other sfx name.

The model lives outside the project in its own venv (docs/ARCHITECTURE.md): $SA3_DIR (default ~/tools/stable-audio-3),
with Stability's repo in sa3-repo/ and weights in the Hugging Face cache. Licence: Stability AI Community License
(free commercial use under $1M yearly revenue after registering with Stability AI).
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "library" / "sfx"
INDEX = ROOT / "library" / "sfx.json"
SA3_DIR = Path(os.environ.get("SA3_DIR", Path.home() / "tools" / "stable-audio-3"))
LICENCE = ("Stability AI Community License (generated locally with Stable Audio 3 Small SFX; "
           "commercial use needs free registration with Stability AI, under $1M yearly revenue)")
LICENCE_URL = "https://stability.ai/community-license-agreement"
NAME_RE = re.compile(r"^[a-z0-9_]{2,40}$")


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _probe(path, what):
    out = _run(["ffprobe", "-v", "error", "-show_entries", what, "-of", "csv=p=0", str(path)]).stdout.strip()
    try:
        return float(out.split(",")[0])
    except ValueError:  # an all-silent sound trims to an empty file: ffprobe says "N/A"
        return 0.0


def _peak_db(path):
    err = _run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"]).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", err)
    if not m:
        raise RuntimeError(f"could not measure peak of {path}")
    return float(m.group(1))


def finish_sound(src, dst, maxlen):
    """Trim silence, mono 44.1 kHz, cap at maxlen, fade out, peak -1 dBFS. Returns the final length."""
    trim = ("silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
            "silenceremove=start_periods=1:start_threshold=-50dB,areverse")
    tmp = Path(str(dst) + ".tmp.wav")
    r = _run(["ffmpeg", "-hide_banner", "-y", "-i", str(src), "-ac", "1", "-ar", "44100",
              "-af", f"{trim},atrim=0:{maxlen}", "-c:a", "pcm_s16le", str(tmp)])
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])
    dur = _probe(tmp, "format=duration")
    if dur < 0.05:
        tmp.unlink()
        raise RuntimeError("sound is (almost) silent after trimming; try another prompt or seed")
    fade = min(0.15, dur * 0.2)
    gain = -1.0 - _peak_db(tmp)
    r = _run(["ffmpeg", "-hide_banner", "-y", "-i", str(tmp), "-af",
              f"afade=t=out:st={dur - fade:.3f}:d={fade:.3f},volume={gain:.2f}dB", "-c:a", "pcm_s16le", str(dst)])
    tmp.unlink()
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])
    out = _probe(dst, "format=duration")
    # self-check: length capped and peak where every library sound sits
    assert 0.05 <= out <= maxlen + 0.02, out
    assert abs(_peak_db(dst) + 1.0) < 0.6, dst
    return out


def generate(prompt, wav, seconds, seed, steps, cfg, negative):
    script = SA3_DIR / "sa3-repo" / "optimized" / "mlx" / "scripts" / "sa3_mlx.py"
    python = SA3_DIR / "bin" / "python"
    if not script.exists() or not python.exists():
        sys.exit(f"Stable Audio 3 not found in {SA3_DIR} (see engine/README.md, 'Local SFX model')")
    cmd = [str(python), str(script), "--prompt", prompt, "--dit", "sm-sfx", "--decoder", "same-s",
           "--seconds", str(seconds), "--out", str(wav)]
    for flag, val in (("--seed", seed), ("--steps", steps)):
        if val is not None:
            cmd += [flag, str(val)]
    if cfg and cfg > 1.0:
        cmd += ["--cfg", str(cfg)]
        if negative:
            cmd += ["--negative-prompt", negative]
    # weights are already in the Hugging Face cache; offline keeps the model from reaching the network
    env = {**os.environ, "HF_HUB_OFFLINE": "1"}
    r = _run(cmd, cwd=script.parent.parent, env=env)
    if r.returncode != 0 or not Path(wav).exists():
        sys.exit("generation failed:\n" + (r.stderr or r.stdout)[-800:])
    m = re.search(r"seed (\d+)", r.stdout + r.stderr)
    return int(m.group(1)) if m else seed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("prompt")
    ap.add_argument("--seconds", type=float, default=2.0)
    ap.add_argument("--maxlen", type=float, default=None, help="cap after trimming (default: --seconds)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--cfg", type=float, default=1.0)
    ap.add_argument("--negative", default="music, speech, voice")
    ap.add_argument("--tags", default="generated")
    ap.add_argument("--mood", default="neutral")
    a = ap.parse_args()

    if not NAME_RE.match(a.name):
        sys.exit("name must be 2-40 chars of a-z, 0-9, _")
    if not 0.3 <= a.seconds <= 10:
        sys.exit("--seconds must be between 0.3 and 10 (sound effects, not music)")
    dst = LIB / f"{a.name}.wav"
    index = json.loads(INDEX.read_text())
    if dst.exists() or any(s["name"] == a.name for s in index["sounds"]):
        sys.exit(f"{a.name} already exists; pick a new name (sounds are never overwritten)")

    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.wav"
        seed = generate(a.prompt, raw, a.seconds, a.seed, a.steps, a.cfg, a.negative)
        length = finish_sound(raw, dst, a.maxlen or a.seconds)

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy(INDEX, INDEX.with_name(f"sfx.json.bak-{stamp}"))
    index["sounds"].append({
        "name": a.name, "tags": [t for t in a.tags.split(",") if t], "mood": a.mood, "loop": False,
        "licence": LICENCE, "licence_url": LICENCE_URL, "source": "engine/tools/gen_sfx.py (Stable Audio 3 Small SFX)",
        "prompt": a.prompt, "seed": seed, "seconds": a.seconds, "cfg": a.cfg,
        "description": f"generated: {a.prompt} (mono 44.1 kHz, peak -1 dBFS, {length:.2f} s)",
    })
    INDEX.write_text(json.dumps(index, indent=1, ensure_ascii=False))
    print(f"ok {dst.relative_to(ROOT)}  {length:.2f} s  seed {seed}")


if __name__ == "__main__":
    main()
