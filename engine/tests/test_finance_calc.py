"""Known-answer tests for finance_calc. Run: engine/.venv/bin/python -m unittest discover engine/tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import finance_calc as fc  # noqa: E402


def data(points, resolution="daily"):
    return {"name": "TEST", "resolution": resolution, "_path": "test.json",
            "series": [{"date": d, "value": v} for d, v in points]}


class Invest(unittest.TestCase):
    def test_simple_gain(self):
        r = fc.invest(data([("2020-01-02", 100), ("2021-01-04", 150)]), 1000, "2020-01-02", "2021-01-04")
        self.assertAlmostEqual(r["value"], 1500)
        self.assertAlmostEqual(r["change"], 0.5)

    def test_weekend_uses_previous_trading_day_and_reports_it(self):
        d = data([("2024-01-05", 100), ("2024-01-08", 110)])  # Fri, Mon
        r = fc.invest(d, 1000, "2024-01-06", "2024-01-08")    # Saturday start
        self.assertEqual(r["start"]["date"], "2024-01-05")

    def test_gap_too_big_is_an_error_not_a_guess(self):
        d = data([("2024-01-02", 100), ("2024-03-01", 110)])
        with self.assertRaises(fc.DataError):
            fc.invest(d, 1000, "2024-01-02", "2024-02-15")

    def test_date_before_data_is_an_error(self):
        with self.assertRaises(fc.DataError):
            fc.change(data([("2024-01-02", 100), ("2024-01-03", 101)]), "2023-12-01", "2024-01-03")


class Drawdown(unittest.TestCase):
    def test_peak_to_trough(self):
        d = data([("2021-01-01", 100), ("2021-06-01", 120), ("2021-09-01", 90),
                  ("2022-01-01", 60), ("2022-06-01", 130)])
        r = fc.drawdown(d, "2021-01-01", "2022-06-01")
        self.assertEqual(r["peak"]["date"], "2021-06-01")
        self.assertEqual(r["trough"]["date"], "2022-01-01")
        self.assertAlmostEqual(r["change"], -0.5)

    def test_later_smaller_drop_does_not_win(self):
        d = data([("2021-01-01", 100), ("2021-02-01", 50), ("2021-03-01", 200), ("2021-04-01", 180)])
        self.assertAlmostEqual(fc.drawdown(d, "2021-01-01", "2021-04-01")["change"], -0.5)

    def test_no_drop_raises(self):
        with self.assertRaises(fc.DataError):
            fc.drawdown(data([("2021-01-01", 1), ("2021-01-02", 2)]), "2021-01-01", "2021-01-02")


class Growth(unittest.TestCase):
    def test_cagr_doubling_in_10_years(self):
        d = data([("2010-01-01", 100), ("2020-01-01", 200)], "monthly")
        self.assertAlmostEqual(fc.cagr(d, "2010-01-01", "2020-01-01")["cagr"], 2 ** 0.1 - 1, places=4)

    def test_cagr_under_one_year_refused(self):
        with self.assertRaises(fc.DataError):
            fc.cagr(data([("2020-01-01", 1), ("2020-06-01", 2)], "monthly"), "2020-01-01", "2020-06-01")

    def test_inflation(self):
        cpi = data([("2000-01-01", 100.0), ("2020-01-01", 130.0)], "monthly")
        self.assertAlmostEqual(fc.inflate(cpi, 1000, "2000-01-01", "2020-01-01")["value"], 1300)


class Saying(unittest.TestCase):
    def test_dollars_three_significant_figures(self):
        self.assertEqual(fc.say_dollars(13912.4), "$13,900")
        self.assertEqual(fc.say_dollars(1000), "$1,000")
        self.assertEqual(fc.say_dollars(2_345_678), "$2,350,000")
        self.assertEqual(fc.say_dollars(5.512), "$5.51")

    def test_pct(self):
        self.assertEqual(fc.say_pct(-0.5934), "59%")
        self.assertEqual(fc.say_multiple(13.9), "14x")
        self.assertEqual(fc.say_multiple(2.34), "2.3x")


class BadData(unittest.TestCase):
    def test_unsorted_or_bad_values_rejected(self):
        import json, tempfile
        for series in ([{"date": "2021-01-02", "value": 1}, {"date": "2021-01-01", "value": 1}],
                       [{"date": "2021-01-01", "value": 0}], []):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
                json.dump({"series": series}, f)
            with self.assertRaises(fc.DataError):
                fc.load(f.name)


if __name__ == "__main__":
    unittest.main()
