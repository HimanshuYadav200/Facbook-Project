"""Tests for voice.py's sentence split (used by --sentence-gap)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import voice  # noqa: E402


class Sentences(unittest.TestCase):
    def test_split_keeps_punctuation_and_short_lines(self):
        self.assertEqual(voice.split_sentences("He asked, how? Time. It's about $41,100. Done!"),
                         ["He asked, how?", "Time.", "It's about $41,100.", "Done!"])

    def test_no_split_inside_numbers_or_commas(self):
        self.assertEqual(voice.split_sentences("He paid 4.5% on $1,000, then left."), ["He paid 4.5% on $1,000, then left."])


class Trim(unittest.TestCase):
    def test_trim_keeps_sound_and_small_margin(self):
        import numpy as np
        a = np.zeros(voice.SR * 2, dtype=np.float32)
        a[voice.SR: voice.SR + 100] = 0.5  # 100 samples of sound after 1 s of silence
        out = voice.trim_silence(a)
        k = int(0.04 * voice.SR)
        self.assertEqual(len(out), 100 + 2 * k)
        self.assertEqual(float(abs(out).max()), 0.5)


if __name__ == "__main__":
    unittest.main()
