"""Narration + word timings for a run: script.txt → voice.wav (Kokoro) → words.json (mlx-whisper).

Usage: engine/.venv/bin/python engine/tools/voice.py runs/<niche>/<id> --voice bm_george --speed 0.95 [--sentence-gap 0.45] [--reuse-voice]

- Caption words always come from script.txt; Whisper only supplies the timing (it misspells names).
- The Kokoro language comes from the voice name's first letter (a = American, b = British, ...).
  The test version always used American, so British voices mispronounced some words.
- Write numbers as digits in the script ("$41,100", "66%", "2016"); Kokoro reads them correctly
  and captions show them as one word. Write "262 times", not "262x" (read as "ex").
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 24000  # Kokoro output sample rate
WHISPER = "mlx-community/whisper-small.en-mlx"
MIN_MATCH = 0.85  # below this share of matched words, the voice probably misread the script


def split_sentences(text):
    """Split after . ? ! (keeping them); 'Time.' stays its own sentence."""
    return [s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if s]


def trim_silence(audio, threshold=0.01, keep=0.04):
    """Cut Kokoro's own lead-in/out silence (it pads every call), keeping a few ms so words aren't clipped."""
    loud = np.flatnonzero(np.abs(audio) > threshold)
    if not len(loud):
        return audio
    k = int(keep * SR)
    return audio[max(0, loud[0] - k): loud[-1] + k + 1]


def make_voice(text, voice, speed, wav_path, sentence_gap=0.0):
    from kokoro import KPipeline
    pipe = KPipeline(lang_code=voice[0])
    if sentence_gap <= 0:
        chunks = [audio for _, _, audio in pipe(text, voice=voice, speed=speed)]
    else:
        # Kokoro runs long text together with almost no pauses; calm styles need a breath between sentences.
        gap = np.zeros(int(sentence_gap * SR), dtype=np.float32)
        chunks = []
        for s in split_sentences(text):
            audio = np.concatenate([np.asarray(a) for _, _, a in pipe(s, voice=voice, speed=speed)])
            chunks += [trim_silence(audio), gap]
        chunks = chunks[:-1]
    if not chunks:
        raise RuntimeError("Kokoro produced no audio")
    audio = np.concatenate([np.asarray(c) for c in chunks])
    sf.write(wav_path, audio, SR)
    return len(audio) / SR


def word_timings(wav_path):
    import mlx_whisper
    result = mlx_whisper.transcribe(str(wav_path), path_or_hf_repo=WHISPER, word_timestamps=True)
    return [{"word": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
            for seg in result["segments"] for w in seg.get("words", [])]


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align_to_script(script_text, heard, duration):
    """Match script words to heard words. Where they differ, spread the heard time span evenly
    over the script words. Returns (words, share of script words matched exactly)."""
    script = script_text.split()
    sm = difflib.SequenceMatcher(a=[_norm(w) for w in script], b=[_norm(h["word"]) for h in heard], autojunk=False)
    out, matched = [], 0
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            matched += a1 - a0
            for i, j in zip(range(a0, a1), range(b0, b1)):
                out.append({"word": script[i], "start": heard[j]["start"], "end": heard[j]["end"]})
        elif a1 > a0:
            if b1 > b0:
                start, end = heard[b0]["start"], heard[b1 - 1]["end"]
            else:  # Whisper skipped these words: squeeze them in after the previous word
                start = out[-1]["end"] if out else 0.0
                end = heard[b0]["start"] if b0 < len(heard) else min(duration, start + 0.3 * (a1 - a0))
            step = max(end - start, 0.01) / (a1 - a0)
            for k, i in enumerate(range(a0, a1)):
                out.append({"word": script[i], "start": round(start + k * step, 3), "end": round(start + (k + 1) * step, 3)})
    # Timings must never go backwards or past the audio.
    for k in range(1, len(out)):
        out[k]["start"] = max(out[k]["start"], out[k - 1]["start"])
    for w in out:
        w["end"] = min(max(w["end"], w["start"]), duration)
    return out, matched / max(1, len(script))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--voice", required=True, help="Kokoro voice, e.g. bm_george, am_puck")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--sentence-gap", type=float, default=0.0,
                    help="seconds of silence between sentences (0 = Kokoro's own pacing; stickman-calm uses ~0.45)")
    ap.add_argument("--reuse-voice", action="store_true", help="only redo timings for an existing voice.wav")
    a = ap.parse_args(argv)
    run = Path(a.run)
    text = (run / "script.txt").read_text().strip()
    if not text:
        print("ERROR: script.txt is empty", file=sys.stderr)
        return 1
    wav = run / "voice.wav"
    if a.reuse_voice and wav.exists():
        dur = sf.info(wav).duration
    else:
        dur = make_voice(text, a.voice, a.speed, wav, a.sentence_gap)
    words, match = align_to_script(text, word_timings(wav), dur)
    (run / "words.json").write_text(json.dumps(
        {"duration": round(dur, 3), "voice": a.voice, "speed": a.speed, "sentence_gap": a.sentence_gap, "match": round(match, 3), "words": words}, indent=1))
    print(f"voice {dur:.2f}s, {len(words)} words, {match:.0%} heard as written -> {run}")
    if match < MIN_MATCH:
        print(f"WARNING: only {match:.0%} of words heard as written. Listen to voice.wav: the voice may have misread "
              "a name or number. Fix the spelling in script.txt and run again.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
