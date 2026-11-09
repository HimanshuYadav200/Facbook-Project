"""Generate simple placeholder sound effects from code (no licences needed).

Usage: python make_sfx.py <output_dir>
Creates whoosh, pop, thud, ding, boing, crash, tick, cash, vinyl bed and room tone as WAV files.
These are test placeholders; a real tagged SFX library replaces them later.
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


def vinyl_bed(sec=40):
    n = int(SR * sec)
    hiss = sweep_noise(sec, 3000, 3000) * 0.05
    crackle = np.zeros(n)
    idx = rng.integers(0, n, int(sec * 25))
    crackle[idx] = rng.uniform(-1, 1, len(idx))
    return norm(hiss + crackle * 0.5, 0.25)


def room_tone(sec=40):
    n = int(SR * sec)
    brown = np.cumsum(rng.standard_normal(n))
    brown -= np.convolve(brown, np.ones(2000) / 2000, mode="same")
    return norm(brown, 0.12)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "sfx")
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in {
        "whoosh": whoosh, "pop": pop, "thud": thud, "ding": ding, "boing": boing,
        "crash": crash, "tick": tick, "cash": cash, "vinyl": vinyl_bed, "room": room_tone,
    }.items():
        sf.write(out / f"{name}.wav", fn().astype(np.float32), SR)
        print("wrote", out / f"{name}.wav")


if __name__ == "__main__":
    main()
