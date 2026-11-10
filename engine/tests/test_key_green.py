"""Tests for key_green: green background removed, character kept, crop tight, green spill removed."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import key_green as kg  # noqa: E402


def scene():
    """200x300 bright green image with a white head (disc) and a dark body, like a cartoon character."""
    img = np.zeros((300, 200, 3), np.int16)
    img[...] = (30, 220, 40)
    yy, xx = np.mgrid[0:300, 0:200]
    img[np.hypot(xx - 100, yy - 80) < 40] = (245, 245, 245)
    img[120:260, 90:110] = (20, 20, 30)
    return img


class KeyGreen(unittest.TestCase):
    def test_background_transparent_character_opaque(self):
        rgba = kg.key(scene())
        self.assertEqual(rgba[0, 0, 3], 0)  # a corner is background
        # The crop starts PAD px before the head's top-left (x 60, y 40), so the head centre (100, 80) is at 40 + PAD.
        self.assertEqual(rgba[40 + kg.PAD, 40 + kg.PAD, 3], 255)

    def test_crop_is_tight(self):
        rgba = kg.key(scene())
        # Character spans x 60-140, y 40-260 → crop ≈ 81+2*PAD wide, 220+2*PAD tall.
        self.assertLessEqual(abs(rgba.shape[1] - (81 + 2 * kg.PAD)), 2)
        self.assertLessEqual(abs(rgba.shape[0] - (220 + 2 * kg.PAD)), 2)

    def test_green_spill_removed(self):
        img = scene()
        img[60:70, 95:105] = (200, 240, 200)  # head lit with a green tint
        rgba = kg.key(img).astype(int)
        r, g, b = rgba[..., 0], rgba[..., 1], rgba[..., 2]
        opaque = rgba[..., 3] > 0
        self.assertTrue((g[opaque] <= np.maximum(r, b)[opaque]).all())

    def test_all_green_gives_none(self):
        img = np.zeros((50, 50, 3), np.int16)
        img[...] = (30, 220, 40)
        self.assertIsNone(kg.key(img))


if __name__ == "__main__":
    unittest.main()
