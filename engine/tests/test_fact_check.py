"""Tests for fact_check's matching (no network): numbers, key terms, independent sites, short queries."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fact_check as fc  # noqa: E402


def reply(*pages):
    return {"results": [{"url": u, "title": "", "content": t} for u, t in pages]}


class FactCheck(unittest.TestCase):
    def test_number_must_appear(self):
        f = {"say": "500,000"}
        self.assertTrue(fc.supports(f, "the bank keeps 500,000 wheels"))
        self.assertFalse(fc.supports(f, "the bank keeps 440,000 wheels"))

    def test_key_terms_must_all_appear(self):
        f = {"say": "Capone handed Lustig $5,000", "key": ["Capone", "Lustig"]}
        self.assertTrue(fc.supports(f, "Al Capone gave Lustig $5,000 for his honesty"))
        self.assertFalse(fc.supports(f, "Lustig got $5,000 from someone"))

    def test_two_pages_of_one_site_are_not_two_sources(self):
        f = {"say": "20,000"}
        r = reply(("https://www.yahoo.com/a", "20,000 rats"), ("https://news.yahoo.com/b", "20,000 rats"))
        self.assertEqual(fc.judge(f, r)[0], "ONE SITE")
        r["results"].append({"url": "https://en.wikipedia.org/x", "title": "", "content": "over 20,000 rats"})
        self.assertEqual(fc.judge(f, r)[0], "CONFIRMED")

    def test_query_uses_search_field_or_short_keywords(self):
        self.assertEqual(fc.query_for({"say": "x", "search": "Lustig Capone"}), "Lustig Capone")
        q = fc.query_for({"say": "Victor Lustig sold the Eiffel Tower", "what": "A long description. More."})
        self.assertLessEqual(len(q.split()), 10)
        self.assertIn("Victor Lustig", q)


if __name__ == "__main__":
    unittest.main()
