"""Tests for find_eyes: eyes found on a drawn stickman head (also with hair over it or round glasses);
eyebrows and closed eyes ignored."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import find_eyes as fe  # noqa: E402


def head(brows=False, closed=False, hair=False, glasses=False):
    """A grey page with one stickman head (white disc, dark outline) at (288, 400), radius 90."""
    g = np.full((fe.H, fe.W), 170.0)
    yy, xx = np.mgrid[0:fe.H, 0:fe.W]
    d = np.hypot(xx - 288, yy - 400)
    g[d < 90] = 250
    g[(d >= 90) & (d < 95)] = 20
    for ex in (258, 318):
        if closed:
            g[398:401, ex - 8:ex + 8] = 20  # a thin line, like a closed eye
        else:
            g[np.hypot(xx - ex, yy - 400) < 6] = 20
        if brows:
            g[378:381, ex - 12:ex + 12] = 20
        if glasses:
            ring = np.hypot(xx - ex, yy - 400)
            g[(ring >= 18) & (ring < 22)] = 20  # a lens rim: cuts the eye off from the rest of the head
    if hair:
        # hair strands drawn across the top of the head: they eat into the white blob (Meta's long-hair women)
        g[(yy < 390) & (d < 86) & ((xx + yy) % 12 < 6)] = 60
    if glasses:
        g[g == 170] = 250  # white page, and a gap in the outline: the head blob runs into the page
        g[300:320, 280:296] = 250
    return g


class FindEyes(unittest.TestCase):
    def test_finds_both_eyes(self):
        faces = fe.find_faces(head())
        self.assertEqual(len(faces), 1)
        xs = sorted(round(x * fe.W) for x, _ in faces[0]["eyes"])
        self.assertEqual(xs, [258, 318])

    def test_eyebrows_are_not_eyes(self):
        ys = [round(y * fe.H) for _, y in fe.find_faces(head(brows=True))[0]["eyes"]]
        self.assertEqual(ys, [400, 400])

    def test_hair_over_head(self):
        xs = sorted(round(x * fe.W) for x, _ in fe.find_faces(head(hair=True))[0]["eyes"])
        self.assertEqual(xs, [258, 318])

    def test_round_glasses(self):
        faces = fe.find_faces(head(glasses=True))
        self.assertEqual(len(faces), 1)
        xs = sorted(round(x * fe.W) for x, _ in faces[0]["eyes"])
        self.assertEqual(xs, [258, 318])

    def test_closed_eyes_give_no_blink(self):
        self.assertEqual(fe.find_faces(head(closed=True)), [])


if __name__ == "__main__":
    unittest.main()
