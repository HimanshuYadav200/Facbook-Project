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

    def test_stale_words_refused(self):
        d = self.make_run("one two three four", [])
        (d / "script.txt").write_text("one two three five")
        errors, _ = cp.check(d, test=True)
        self.assertTrue(any("script changed" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
