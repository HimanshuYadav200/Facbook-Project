"""Tests for check_plan: number reading and the main refusals."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_plan as cp  # noqa: E402


class Numbers(unittest.TestCase):
    def nums(self, text):
        return [(u, v) for _, u, v in cp.parse_numbers(text)]

    def test_money_percent_multiples(self):
        self.assertEqual(self.nums("It was $41,100, then fell 66%. Up 262 times."),
                         [("$", 41100.0), ("%", 66.0), ("x", 262.0)])

    def test_k_suffix_and_decimals(self):
        self.assertEqual(self.nums("$262K and 4.5%"), [("$", 262000.0), ("%", 4.5)])

    def test_million_billion_words(self):
        self.assertEqual(self.nums("$365 million, then 2.5 billion, but 3 billionaires."),
                         [("$", 365e6), ("", 2.5e9), ("", 3.0)])

    def test_years_and_hyphenated_names_ignored(self):
        self.assertEqual(self.nums("In 2016, COVID-19 hit in 2020."), [])

    def test_sticker_matches_fact_say(self):
        known = cp.fact_numbers([{"say": "$262,000", "also": {"change": "26100%"}}])
        self.assertTrue(cp.matches("$", 262000.0, known))
        self.assertFalse(cp.matches("$", 287000.0, known))


class Refusals(unittest.TestCase):
    def make_run(self, script, facts, shots_from=(0, 3)):
        d = Path(tempfile.mkdtemp())
        words = [{"word": w, "start": i * 0.6, "end": i * 0.6 + 0.5} for i, w in enumerate(script.split())]
        (d / "script.txt").write_text(script)
        (d / "words.json").write_text(json.dumps({"duration": len(words) * 0.6, "words": words}))
        (d / "facts.json").write_text(json.dumps(facts))
        shots = [{"from": f, "bg": "#fff", "layers": []} for f in shots_from]
        (d / "plan.json").write_text(json.dumps({"version": 1, "style": "flat-fastcut", "shots": shots}))
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [1, 2], "styles": ["flat-fastcut"],
                                                   "banned": ["guaranteed"]}))
        return d

    def test_unsourced_number_refused(self):
        errors, _ = cp.check(self.make_run("He had $1,000 then $400.", []), test=True)
        self.assertTrue(any('"$1,000" is not in facts.json' in e for e in errors))

    def test_illustrative_story_numbers_allowed(self):
        facts = [{"id": "a", "say": "$1,000", "kind": "illustrative"}, {"id": "b", "say": "$400", "kind": "illustrative"}]
        errors, _ = cp.check(self.make_run("He had $1,000 then $400.", facts), test=True)
        self.assertEqual(errors, [])

    def test_spelled_amounts_and_banned_phrases_refused(self):
        errors, _ = cp.check(self.make_run("Guaranteed forty thousand dollars here.", []), test=True)
        self.assertTrue(any("banned phrase" in e for e in errors))
        self.assertTrue(any("digits" in e for e in errors))

    def test_million_after_digits_allowed_and_checked(self):
        facts = [{"id": "a", "say": "$365 million", "source": "https://example.org"}]
        errors, _ = cp.check(self.make_run("They lost $365 million that year.", facts), test=True)
        self.assertEqual(errors, [])
        errors, _ = cp.check(self.make_run("They lost $380 million that year.", facts), test=True)
        self.assertTrue(any('"$380 million" is not in facts.json' in e for e in errors))

    def test_stale_words_refused(self):
        d = self.make_run("one two three four", [])
        (d / "script.txt").write_text("one two three five")
        errors, _ = cp.check(d, test=True)
        self.assertTrue(any("script changed" in e for e in errors))


class NicheRules(unittest.TestCase):
    """Each run follows its own niche.json: length, styles and banned words."""
    make_run = Refusals.make_run

    def test_missing_niche_json_refused(self):
        d = self.make_run("one two three four", [])
        (d / "niche.json").unlink()
        errors, _ = cp.check(d, test=True)
        self.assertTrue(any("niche.json missing" in e for e in errors))

    def test_length_comes_from_niche(self):
        d = self.make_run("one two three four", [])  # 4 words x 0.6 s + 0.5 s tail = 2.9 s
        errors, _ = cp.check(d)
        self.assertTrue(any("outside 1-2s" in e for e in errors))
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [2, 4], "styles": ["flat-fastcut"]}))
        errors, _ = cp.check(d)
        self.assertFalse(any("total length" in e for e in errors))

    def test_style_not_in_niche_refused(self):
        d = self.make_run("one two three four", [])
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [1, 9], "styles": ["vintage-story"]}))
        errors, _ = cp.check(d, test=True)
        self.assertTrue(any("not used by niche" in e for e in errors))

    def test_banned_list_is_per_niche(self):
        d = self.make_run("Guaranteed calm story here.", [])
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [1, 9], "styles": ["flat-fastcut"]}))
        errors, _ = cp.check(d, test=True)
        self.assertFalse(any("banned phrase" in e for e in errors))


class StickmanClips(unittest.TestCase):
    """stickman-calm: an animated clip shot may not last longer than its clip."""

    def make_run(self, clip_seconds):
        import subprocess
        d = Path(tempfile.mkdtemp())
        words = [{"word": f"w{i}", "start": i * 1.0, "end": i * 1.0 + 0.8} for i in range(8)]
        (d / "script.txt").write_text(" ".join(w["word"] for w in words))
        (d / "words.json").write_text(json.dumps({"duration": 8.0, "words": words}))
        (d / "facts.json").write_text("[]")
        (d / "img").mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=gray:s=64x112:d={clip_seconds}",
                        str(d / "img" / "c.mp4")], check=True)
        shots = [{"from": 0, "type": "clip", "clip": "c.mp4"}, {"from": 6, "type": "clip", "clip": "c.mp4"}]
        (d / "plan.json").write_text(json.dumps({"version": 1, "style": "stickman-calm", "shots": shots}))
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [1, 99], "styles": ["stickman-calm"]}))
        return d

    def test_clip_long_enough_passes(self):
        errors, _ = cp.check(self.make_run(7), test=True)  # shot 0 lasts 6 s
        self.assertEqual(errors, [])

    def test_clip_too_short_refused(self):
        errors, _ = cp.check(self.make_run(5), test=True)
        self.assertTrue(any("is only 5.00s" in e for e in errors))


class ExplainerShots(unittest.TestCase):
    """explainer-fast: camera moves, cut-out actors and their entry words are checked."""

    def make_run(self, shot1, shot0=None):
        d = Path(tempfile.mkdtemp())
        words = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(8)]
        (d / "script.txt").write_text(" ".join(w["word"] for w in words))
        (d / "words.json").write_text(json.dumps({"duration": 4.0, "words": words}))
        (d / "facts.json").write_text("[]")
        (d / "img").mkdir()
        for f in ("bg.webp", "hero.png"):
            (d / "img" / f).write_bytes(b"x")
        shots = [dict({"from": 0, "img": "bg.webp", "cam": "dive"}, **(shot0 or {})), dict({"from": 4, "img": "bg.webp"}, **shot1)]
        (d / "plan.json").write_text(json.dumps({"version": 1, "style": "explainer-fast", "shots": shots}))
        (d / "niche.json").write_text(json.dumps({"niche": "t", "length_seconds": [1, 99], "styles": ["explainer-fast"]}))
        return d

    def test_good_shot_passes(self):
        actor = {"img": "hero.png", "x": 0.5, "y": 0.9, "h": 0.5, "enter": "slideL", "idle": "wobble", "at": 5}
        errors, _ = cp.check(self.make_run({"cam": "orbitL", "fx": ["flash"], "actors": [actor]}), test=True)
        self.assertEqual(errors, [])

    def test_bad_cam_fx_and_missing_cutout_refused(self):
        actor = {"img": "nobody.png", "x": 0.5, "y": 0.9, "h": 0.5, "dance": True}
        errors, _ = cp.check(self.make_run({"cam": "spin", "fx": ["explode"], "actors": [actor]}), test=True)
        text = " ".join(errors)
        for bit in ("unknown cam 'spin'", "unknown fx 'explode'", "img/nobody.png missing", "unknown field 'dance'"):
            self.assertIn(bit, text)

    def test_actor_entering_outside_its_shot_refused(self):
        actor = {"img": "hero.png", "x": 0.5, "y": 0.9, "h": 0.5, "at": 2}
        errors, _ = cp.check(self.make_run({"actors": [actor]}), test=True)
        self.assertTrue(any("enters at word 2, outside this shot" in e for e in errors))

    def test_good_graphics_and_colour_card_pass(self):
        mg = [{"type": "stamp", "text": "SOLD!", "y": 0.3, "at": 5}, {"type": "money", "dir": "rain"},
              {"type": "pointer", "x": 0.4, "y": 0.5, "dir": "up"}]
        errors, warnings = cp.check(self.make_run({"img": None, "bg": "#2f8f46", "mg": mg}), test=True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_bad_graphics_refused(self):
        mg = [{"type": "confetti"}, {"type": "stamp"}, {"type": "counter", "text": "TONS"},
              {"type": "arrow", "dir": "left"}, {"type": "label", "text": "HI", "at": 1}]
        errors, _ = cp.check(self.make_run({"mg": mg}), test=True)
        text = " ".join(errors)
        for bit in ("unknown type 'confetti'", "stamp needs 'text'", "counter needs a number 'to'",
                    "dir 'left' not allowed for arrow", "appears at word 1, outside this shot"):
            self.assertIn(bit, text)

    def test_graphic_numbers_must_be_in_facts(self):
        mg = [{"type": "counter", "to": 7300, "text": "tons"}, {"type": "label", "text": "60 TONS"}]
        errors, _ = cp.check(self.make_run({"mg": mg}), test=True)
        self.assertTrue(any('"7,300" is not in facts.json' in e for e in errors))
        self.assertTrue(any('"60" is not in facts.json' in e for e in errors))

    def test_graphic_seen_too_briefly_refused_and_hold_fixes_it(self):
        late = {"mg": [{"type": "stamp", "text": "SOLD!", "at": 3}]}  # word 3 at 1.5 s, cut at 2.0 s
        errors, _ = cp.check(self.make_run({}, late), test=True)
        self.assertTrue(any("on screen only 0.50s" in e for e in errors))
        errors, _ = cp.check(self.make_run({"hold": 0.5}, late), test=True)
        self.assertEqual(errors, [])
        errors, _ = cp.check(self.make_run({"hold": 0.9}), test=True)
        self.assertTrue(any("hold 0.9 outside" in e for e in errors))

    def test_sound_pools_accepted_and_every_pool_file_exists(self):
        errors, _ = cp.check(self.make_run({"sfx": "crowd_laugh", "cutSfx": "whip", "mg": [{"type": "label", "text": "HI", "sfx": "stamp"}]}), test=True)
        self.assertEqual(errors, [])
        for pool, files in cp.SOUND_POOLS.items():
            for f in files:
                self.assertTrue((cp.ROOT / "library" / "sfx" / f"{f}.wav").exists(), f"pool {pool}: {f}.wav missing")

    def test_text_graphic_on_caption_warns(self):
        _, warnings = cp.check(self.make_run({"mg": [{"type": "label", "text": "HI", "y": 0.72}]}), test=True)
        self.assertTrue(any("sits on the caption" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
