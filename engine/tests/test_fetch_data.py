"""Offline tests for fetch_data: fake API replies, no network. Each one covers a bug the old research code had."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fetch_data as fd  # noqa: E402

FAKE = Path("/nonexistent/cache.json")


def fake_get(reply):
    """Stand-in for get_json that runs the real validator on a canned reply."""
    def _get(source, url, params, headers=None, validate=None, max_age_days=1):
        if validate:
            validate(reply)
        return reply, FAKE
    return _get


class AlphaVantage(unittest.TestCase):
    def setUp(self):
        mock.patch.object(fd, "env", return_value="k").start()
        self.addCleanup(mock.patch.stopall)

    def test_rate_limit_reply_is_an_error(self):
        reply = {"Information": "Thank you for using Alpha Vantage! Please consider spreading out..."}
        with mock.patch.object(fd, "get_json", fake_get(reply)):
            with self.assertRaises(fd.FetchError):
                fd.av_adjusted("NVDA", "weekly")

    def test_wrong_symbol_in_reply_is_an_error(self):
        reply = {"Meta Data": {"2. Symbol": "SPY"}, "Weekly Adjusted Time Series": {}}
        with mock.patch.object(fd, "get_json", fake_get(reply)):
            with self.assertRaises(fd.FetchError):
                fd.av_adjusted("AMZN", "weekly")

    def test_uses_adjusted_not_raw_close(self):
        reply = {"Meta Data": {"2. Symbol": "NVDA"}, "Weekly Adjusted Time Series": {
            "2024-06-07": {"4. close": "1208.88", "5. adjusted close": "120.80"}}}
        with mock.patch.object(fd, "get_json", fake_get(reply)):
            data, _ = fd.av_adjusted("NVDA", "weekly")
        self.assertEqual(data["series"][0]["value"], 120.80)


class Fred(unittest.TestCase):
    def test_missing_dot_values_skipped(self):
        replies = iter([
            {"seriess": [{"title": "CPI", "units": "Index", "frequency_short": "M", "seasonal_adjustment_short": "SA"}]},
            {"observations": [{"date": "2020-01-01", "value": "258.6"}, {"date": "2020-02-01", "value": "."}]},
        ])
        with mock.patch.object(fd, "env", return_value="k"), \
             mock.patch.object(fd, "get_json", lambda *a, **k: (next(replies), FAKE)):
            data, _ = fd.fred("CPIAUCSL")
        self.assertEqual(len(data["series"]), 1)
        self.assertEqual(data["resolution"], "monthly")

    def test_error_reply_is_an_error(self):
        with mock.patch.object(fd, "env", return_value="k"), \
             mock.patch.object(fd, "get_json", fake_get({"error_message": "Bad Request. The series does not exist."})):
            with self.assertRaises(fd.FetchError):
                fd.fred("NOPE")


class CrossCheck(unittest.TestCase):
    def series(self, vals):
        return {"series": [{"date": f"2024-01-{i + 1:02d}", "value": v} for i, v in enumerate(vals)]}

    def test_same_shape_different_scale_agrees(self):
        a = self.series([10 + i for i in range(12)])
        b = self.series([(10 + i) * 0.98 for i in range(12)])  # e.g. slightly different dividend base
        diff, _, n = fd.compare(a, b)
        self.assertLess(diff, 1e-9)
        self.assertEqual(n, 12)

    def test_real_disagreement_found(self):
        a = self.series([10 + i for i in range(12)])
        b = self.series([10 + i for i in range(12)])
        b["series"][0]["value"] = 5  # e.g. one source missed a split
        diff, worst, _ = fd.compare(a, b)
        self.assertGreater(diff, 0.5)
        self.assertEqual(worst, "2024-01-01")


if __name__ == "__main__":
    unittest.main()
