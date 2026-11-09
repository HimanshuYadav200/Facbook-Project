"""Make narration with Kokoro TTS, then get word timings with mlx-whisper.

Usage: python voice_and_timing.py <script.txt> <out_dir> [voice] [speed] [--reuse-voice]
Writes <out_dir>/voice.wav and <out_dir>/words.json ([{word, start, end}] in seconds).
Caption words always come from the script; Whisper only supplies the timing.
"""
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline
import mlx_whisper

SR = 24000  # Kokoro output sample rate


def make_voice(text, voice, speed, wav_path):
    pipe = KPipeline(lang_code="a")  # "a" = American English
    chunks = [audio for _, _, audio in pipe(text, voice=voice, speed=speed)]
    audio = np.concatenate([np.asarray(c) for c in chunks])
    sf.write(wav_path, audio, SR)
    return len(audio) / SR


def word_timings(wav_path):
    result = mlx_whisper.transcribe(
        str(wav_path),
        path_or_hf_repo="mlx-community/whisper-small.en-mlx",
        word_timestamps=True,
    )
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)})
    return words


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align_to_script(script_text, heard):
    """Captions must show the script's words, not what Whisper thought it heard.
    Match the two word lists; where they differ, spread the heard time span evenly
    over the script words."""
    script = script_text.split()
    sm = difflib.SequenceMatcher(a=[_norm(w) for w in script], b=[_norm(h["word"]) for h in heard], autojunk=False)
    out = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for i, j in zip(range(a0, a1), range(b0, b1)):
                out.append({"word": script[i], "start": heard[j]["start"], "end": heard[j]["end"]})
        elif a1 > a0:
            if b1 > b0:
                start, end = heard[b0]["start"], heard[b1 - 1]["end"]
            else:  # Whisper skipped these words: squeeze them in after the previous word
                start = out[-1]["end"] if out else 0.0
                end = heard[b0]["start"] if b0 < len(heard) else start + 0.3 * (a1 - a0)
            step = max(end - start, 0.01) / (a1 - a0)
            for k, i in enumerate(range(a0, a1)):
                out.append({"word": script[i], "start": round(start + k * step, 3), "end": round(start + (k + 1) * step, 3)})
    return out


def main():
    script_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
    speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    out_dir.mkdir(parents=True, exist_ok=True)
    text = script_path.read_text().strip()
    wav = out_dir / "voice.wav"
    if "--reuse-voice" in sys.argv and wav.exists():
        dur = sf.info(wav).duration
    else:
        dur = make_voice(text, voice, speed, wav)
    words = align_to_script(text, word_timings(wav))
    (out_dir / "words.json").write_text(json.dumps({"duration": round(dur, 3), "words": words}, indent=1))
    print(f"voice {dur:.2f}s, {len(words)} words -> {out_dir}")


if __name__ == "__main__":
    main()
