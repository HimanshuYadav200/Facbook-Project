"""Generate simple placeholder sound effects from code (no licences needed).

Usage: engine/.venv/bin/python engine/tools/make_sfx.py [output_dir]   (default: library/sfx)
Creates whoosh, pop, thud, ding, boing, crash, tick, cash, vinyl bed, room tone, and the explainer-fast set
(swoosh1-4, riser, impact, sparkle, click, slide, crowd_laugh, crowd_whoa via Kokoro) as WAV files.
Files that already exist are skipped (never overwritten).
These are placeholders; real, licensed SFX get added to library/sfx with an entry in library/sfx.json.
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
rng = np.random.default_rng(7)


def t(sec):
    return np.linspace(0, sec, int(SR * sec), endpoint=False)


def env(n, attack=0.01, release=None):
    """Simple attack + exponential decay envelope."""
    a = max(1, int(SR * attack))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    if release:
        e[a:] = np.exp(-np.linspace(0, release, n - a))
    return e


def sweep_noise(sec, f0, f1):
    """Noise filtered by a moving one-pole lowpass: the base of a whoosh."""
    n = int(SR * sec)
    noise = rng.standard_normal(n)
    cut = np.geomspace(f0, f1, n)
    alpha = 1 - np.exp(-2 * np.pi * cut / SR)
    out = np.zeros(n)
    y = 0.0
    for i in range(n):
        y += alpha[i] * (noise[i] - y)
        out[i] = y
    return out


def norm(x, peak=0.9):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def whoosh():
    x = sweep_noise(0.35, 300, 6000)
    shape = np.sin(np.linspace(0, np.pi, len(x))) ** 2
    return norm(x * shape, 0.7)


def pop():
    tt = t(0.09)
    f = np.linspace(500, 1300, len(tt))
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.002, 6))


def thud():
    tt = t(0.3)
    f = np.linspace(110, 40, len(tt))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = rng.standard_normal(len(tt)) * np.exp(-np.linspace(0, 60, len(tt)))
    return norm((body + 0.3 * click) * env(len(tt), 0.002, 7))


def ding(freq=1568):
    tt = t(0.9)
    x = sum(a * np.sin(2 * np.pi * freq * h * tt) for h, a in [(1, 1), (2.76, 0.4), (5.4, 0.2)])
    return norm(x * env(len(tt), 0.003, 5), 0.6)


def boing():
    tt = t(0.45)
    f = 220 + 180 * np.exp(-tt * 6) * np.sin(2 * np.pi * 14 * tt)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.005, 4), 0.7)


def crash():
    n = int(SR * 0.7)
    x = rng.standard_normal(n) * np.exp(-np.linspace(0, 6, n))
    low = np.sin(2 * np.pi * 60 * t(0.7)) * np.exp(-np.linspace(0, 10, n))
    return norm(x * 0.6 + low)


def tick():
    n = int(SR * 0.03)
    return norm(rng.standard_normal(n) * np.exp(-np.linspace(0, 40, n)), 0.5)


def cash():
    a = ding(2093)[: int(SR * 0.25)]
    b = ding(2637)
    gap = np.zeros(int(SR * 0.06))
    rattle = rng.standard_normal(int(SR * 0.12)) * 0.15
    return norm(np.concatenate([rattle, a, gap, b]), 0.6)


def loop_edges(x, ms=60):
    """Fade both ends so a looping bed doesn't click where it restarts."""
    k = int(SR * ms / 1000)
    ramp = np.linspace(0, 1, k)
    x = x.copy()
    x[:k] *= ramp
    x[-k:] *= ramp[::-1]
    return x


def vinyl_bed(sec=40):
    n = int(SR * sec)
    hiss = sweep_noise(sec, 3000, 3000) * 0.05
    crackle = np.zeros(n)
    idx = rng.integers(0, n, int(sec * 25))
    crackle[idx] = rng.uniform(-1, 1, len(idx))
    return loop_edges(norm(hiss + crackle * 0.5, 0.25))


def room_tone(sec=40):
    n = int(SR * sec)
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.convolve(brown, np.ones(2000) / 2000, mode="same")
    return loop_edges(norm(brown, 0.12))


# --- explainer-fast set (2026-11-10): one hit per shot, so several variants that don't sound repeated ---
# Each uses its own seeded generator, so making one never changes another.

def swoosh(sec, f0, f1, seed, peak=0.7):
    """Air whoosh: filtered noise sweeping f0 -> f1, fast rise and a longer tail (feels like a camera move)."""
    global rng
    rng = np.random.default_rng(seed)
    x = sweep_noise(sec, f0, f1)
    n = len(x)
    rise = int(n * 0.35)
    shape = np.concatenate([np.linspace(0, 1, rise) ** 2, np.exp(-np.linspace(0, 4, n - rise))])
    return norm(x * shape, peak)


def riser():
    """Rising tone + noise for 1.2 s: tension before a reveal."""
    global rng
    rng = np.random.default_rng(21)
    tt = t(1.2)
    f = np.geomspace(180, 1400, len(tt))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    air = sweep_noise(1.2, 400, 8000) * 0.8
    shape = np.linspace(0, 1, len(tt)) ** 2
    shape[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return norm((tone + air) * shape, 0.7)


def impact():
    """Deep boom + crack: a big reveal or something falling."""
    global rng
    rng = np.random.default_rng(22)
    tt = t(0.9)
    body = np.sin(2 * np.pi * np.cumsum(np.geomspace(90, 30, len(tt))) / SR) * np.exp(-tt * 5)
    crack = rng.standard_normal(len(tt)) * np.exp(-tt * 40)
    return norm(body + 0.5 * crack)


def sparkle():
    """Quick rising bell notes: an idea, a shiny object, money appearing."""
    notes = [1760, 2217, 2637, 3520]
    out = np.zeros(int(SR * 0.7))
    for k, f in enumerate(notes):
        tt = t(0.4)
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 12) * (0.6 + 0.1 * k)
        a = int(k * 0.06 * SR)
        out[a:a + len(s)] += s
    return norm(out, 0.5)


def click():
    """Camera shutter / stamp click: two tiny noise bursts."""
    global rng
    rng = np.random.default_rng(23)
    b = lambda: rng.standard_normal(int(SR * 0.012)) * np.exp(-np.linspace(0, 8, int(SR * 0.012)))
    return norm(np.concatenate([b(), np.zeros(int(SR * 0.05)), b() * 0.7]), 0.6)


def slide():
    """Paper / object sliding across a table: soft band-passed noise, 0.5 s."""
    global rng
    rng = np.random.default_rng(24)
    x = sweep_noise(0.5, 1500, 2500) - sweep_noise(0.5, 300, 500)
    return norm(x * np.sin(np.linspace(0, np.pi, len(x))), 0.4)


def kokoro_crowd(line, voices, seed):
    """A few Kokoro voices saying the same short reaction, offset and panned to sound like a small crowd.
    shortcut: synthetic voices, a bit robotic; swap for a CC0 crowd recording when we add a pack."""
    from kokoro import KPipeline
    from scipy.signal import resample_poly
    r = np.random.default_rng(seed)
    pipes, tracks = {}, []
    for v in voices:
        p = pipes.setdefault(v[0], KPipeline(lang_code=v[0]))
        a = np.concatenate([np.asarray(x) for _, _, x in p(line, voice=v, speed=1.15 + 0.15 * r.random())])
        tracks.append(resample_poly(a.astype(np.float64), 147, 80))  # 24 kHz -> 44.1 kHz
    n = max(len(a) for a in tracks) + int(0.3 * SR)
    st = np.zeros((n, 2))
    for a in tracks:
        off, pan = int(r.uniform(0, 0.25) * SR), r.uniform(0.2, 0.8)
        st[off:off + len(a), 0] += a * (1 - pan)
        st[off:off + len(a), 1] += a * pan
    return norm(st, 0.6)


NEW = {
    "swoosh1": lambda: swoosh(0.30, 400, 7000, 11),
    "swoosh2": lambda: swoosh(0.45, 250, 5000, 12),
    "swoosh3": lambda: swoosh(0.22, 800, 9000, 13, 0.6),
    "swoosh4": lambda: swoosh(0.60, 6000, 300, 14),  # falling: camera dives down
    "riser": riser, "impact": impact, "sparkle": sparkle, "click": click, "slide": slide,
    "crowd_laugh": lambda: kokoro_crowd("Ha ha ha ha!", ["am_adam", "am_echo", "am_michael", "af_bella", "am_eric"], 31),
    "crowd_whoa": lambda: kokoro_crowd("Whoa!", ["am_adam", "am_liam", "af_nicole", "am_onyx"], 32),
}


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "library" / "sfx"
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in {
        "whoosh": whoosh, "pop": pop, "thud": thud, "ding": ding, "boing": boing,
        "crash": crash, "tick": tick, "cash": cash, "vinyl": vinyl_bed, "room": room_tone,
    }.items():
        if (out / f"{name}.wav").exists():
            continue  # never overwrite a sound already in use
        sf.write(out / f"{name}.wav", fn().astype(np.float32), SR)
        print("wrote", out / f"{name}.wav")
    for name, fn in NEW.items():
        if (out / f"{name}.wav").exists():
            continue
        sf.write(out / f"{name}.wav", fn().astype(np.float32), SR)
        print("wrote", out / f"{name}.wav")


if __name__ == "__main__":
    main()
