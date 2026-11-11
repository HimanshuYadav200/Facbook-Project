"""Tests for match_images: by-name matching, both prompt formats, g_* to img/green/, conflicts, time-order fallback."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import match_images as mi  # noqa: E402


def make_run(td, prompts, files):
    run = Path(td)
    (run / "incoming").mkdir()
    (run / "image_prompts.txt").write_text(prompts)
    for i, name in enumerate(files):
        p = run / "incoming" / name
        p.write_bytes(f"image {name}".encode())  # different bytes per file, so no duplicates
        os.utime(p, (1000 + i, 1000 + i))  # file time = list order
    return run


class MatchImages(unittest.TestCase):
    def test_by_name_ignores_download_order(self):
        with tempfile.TemporaryDirectory() as td:
            # saved in the wrong order on purpose: names must win over file times
            run = make_run(td, "s_two: b\ns_one | a\ng_hero: c\n", ["x_s_one.webp", "x_g_hero.png", "x_s_two.webp"])
            self.assertEqual(mi.main([str(run)]), 0)
            self.assertEqual(sorted(p.name for p in (run / "img").glob("*.*")), ["s_one.webp", "s_two.webp"])
            self.assertTrue((run / "img" / "green" / "g_hero.png").exists())

    def test_longest_name_wins(self):
        self.assertEqual(mi.name_of(Path("m_s_vault_door (1).webp"), ["door", "s_vault_door"]), "s_vault_door")

    def test_two_files_for_one_name_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            run = make_run(td, "s_one: a\n", ["x_s_one.webp", "x_s_one (1).webp"])
            self.assertEqual(mi.main([str(run)]), 1)
            self.assertEqual(len(list((run / "incoming").iterdir())), 2)  # nothing moved

    def test_unnamed_files_fill_gaps_by_time(self):
        with tempfile.TemporaryDirectory() as td:
            run = make_run(td, "a1: x\nb2: y\n", ["download.webp", "download2.webp"])
            self.assertEqual(mi.main([str(run)]), 0)
            self.assertEqual((run / "img" / "a1.webp").read_bytes(), b"image download.webp")

    def test_second_run_fills_only_the_gaps(self):
        with tempfile.TemporaryDirectory() as td:
            run = make_run(td, "a1: x\nb2: y\n", ["p_a1.webp"])
            self.assertEqual(mi.main([str(run)]), 1)  # b2 missing
            (run / "incoming" / "p_b2.webp").write_bytes(b"later")
            self.assertEqual(mi.main([str(run)]), 0)
            self.assertTrue((run / "img" / "b2.webp").exists())


if __name__ == "__main__":
    unittest.main()
