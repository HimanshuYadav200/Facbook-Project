"""Tests for gen_sfx.finish_sound: silence trimmed, length capped, peak at -1 dBFS, silent input refused.
The model itself is not run here (needs ~/tools/stable-audio-3); only the shared clean-up step."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import gen_sfx  # noqa: E402


def make_wav(path, filtergraph, seconds):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", filtergraph, "-t", str(seconds),
                    "-ac", "2", "-ar", "48000", str(path)], check=True)


class FinishSound(unittest.TestCase):
    def test_trim_cap_and_peak(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td) / "in.wav", Path(td) / "out.wav"
            # 0.5 s silence, then a quiet 3 s tone: must be trimmed, capped at 1.2 s and raised to -1 dBFS
            make_wav(src, "aevalsrc='if(lt(t,0.5),0,0.1*sin(2*PI*440*t))':s=48000", 3.5)
            length = gen_sfx.finish_sound(src, dst, maxlen=1.2)
            self.assertAlmostEqual(length, 1.2, delta=0.03)
            self.assertAlmostEqual(gen_sfx._peak_db(dst), -1.0, delta=0.6)
            info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=channels,sample_rate",
                                   "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout.strip()
            self.assertEqual(info, "44100,1")

    def test_silent_input_refused(self):
        with tempfile.TemporaryDirectory() as td:
            src, dst = Path(td) / "in.wav", Path(td) / "out.wav"
            make_wav(src, "anullsrc=r=48000:cl=stereo", 1.0)
            with self.assertRaises(RuntimeError):
                gen_sfx.finish_sound(src, dst, maxlen=1.0)
            self.assertFalse(dst.exists())


if __name__ == "__main__":
    unittest.main()
