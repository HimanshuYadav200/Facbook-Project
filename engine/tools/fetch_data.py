"""Fetch official data into a run's data/ folder, in the one format finance_calc.py reads.

Commands:
  prices <TICKER> <out.json> [--source tiingo|av-weekly|av-monthly] [--check av-weekly|none]
      Split- and dividend-adjusted closes. Default: Tiingo daily, cross-checked with Alpha Vantage weekly.
  crypto <SYMBOL> <out.json>          Alpha Vantage daily close in USD (one exchange feed: say "about")
  fred   <SERIES_ID> <out.json>       FRED series (e.g. CPIAUCSL, FEDFUNDS, MORTGAGE30US, UNRATE)
  sec    <TICKER> <CONCEPT> <out.json>  SEC EDGAR annual (10-K) values, e.g. Revenues, NetIncomeLoss

Rules (lessons from the old research_agent.py, see docs/RESEARCH_REVIEW.md):
  - The ticker is used exactly as given. Nothing is guessed.
  - Error / rate-limit replies stop the script and are never cached.
  - Raw replies are copied next to the output (data/raw/) so every number can be re-checked later.
  - Keys come from the project .env and are never printed.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import date, datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "engine" / "cache"
TIMEOUT = 30
CHECK_TOLERANCE = 0.01  # 1%: owner's rule; bigger difference between sources = stop


class FetchError(Exception):
    pass


# ---------- keys and cache ----------

def env(name, required=True):
    """Read a key from the environment or the project .env (simple KEY=VALUE lines)."""
    if os.environ.get(name):
        return os.environ[name]
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            if line.strip().startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    if required:
        raise FetchError(f"{name} is not set in .env")
    return None


def _cache_path(source, params):
    safe = {k: v for k, v in params.items() if "key" not in k.lower() and k != "token"}
    h = hashlib.sha1(json.dumps([source, safe], sort_keys=True).encode()).hexdigest()[:16]
    return CACHE / source / f"{h}.json"


def get_json(source, url, params, headers=None, validate=None, max_age_days=1):
    """GET with a file cache. `validate(reply)` must raise FetchError on a bad reply; bad replies are never saved."""
    path = _cache_path(source, {"url": url, **params})
    if path.exists() and (time.time() - path.stat().st_mtime) < max_age_days * 86400:
        return json.loads(path.read_text()), path
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    if r.status_code != 200:
        raise FetchError(f"{source}: HTTP {r.status_code}")
    reply = r.json()
    if validate:
        validate(reply)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reply))
    return reply, path


def write_out(out, data, raw_paths):
    out = Path(out)
    raw_dir = out.parent / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    data["raw_files"] = []
    for p in raw_paths:
        dst = raw_dir / f"{out.stem}.{p.parent.name}.{p.name}"
        shutil.copyfile(p, dst)
        data["raw_files"].append(str(dst.relative_to(out.parent)))
    data["fetched"] = date.today().isoformat()
    out.write_text(json.dumps(data, indent=1))
    s = data["series"]
    print(f"{out}: {len(s)} points {s[0]['date']} → {s[-1]['date']} · {data['source']} · check: {data.get('check')}")


# ---------- sources ----------

def _av_validate(reply):
    for k in ("Error Message", "Information", "Note"):
        if k in reply:
            raise FetchError(f"Alpha Vantage refused: {str(reply[k])[:120]}")


def av_adjusted(ticker, resolution):
    fn = {"weekly": "TIME_SERIES_WEEKLY_ADJUSTED", "monthly": "TIME_SERIES_MONTHLY_ADJUSTED"}[resolution]
    reply, path = get_json("alphavantage", "https://www.alphavantage.co/query",
                           {"function": fn, "symbol": ticker, "apikey": env("ALPHA_VANTAGE_API_KEY")},
                           validate=_av_validate)
    key = next((k for k in reply if "Time Series" in k), None)
    if not key:
        raise FetchError("Alpha Vantage: no time series in reply")
    sym = reply.get("Meta Data", {}).get("2. Symbol", "")
    if sym.upper() != ticker.upper():
        raise FetchError(f"Alpha Vantage returned {sym!r}, asked for {ticker!r}")
    # "5. adjusted close" = split + dividend adjusted. "4. close" (what the old code used) is NOT adjusted.
    series = sorted(({"date": d, "value": float(v["5. adjusted close"])} for d, v in reply[key].items()),
                    key=lambda p: p["date"])
    return {"name": ticker.upper(), "source": f"Alpha Vantage {fn}", "basis": "adjusted close (splits + dividends)",
            "resolution": resolution, "series": series}, path


def tiingo_daily(ticker):
    token = env("TIINGO_API_KEY")

    def validate(reply):
        if isinstance(reply, dict):
            raise FetchError(f"Tiingo refused: {str(reply.get('detail', reply))[:120]}")
        if not reply:
            raise FetchError(f"Tiingo: no data for {ticker}")

    reply, path = get_json("tiingo", f"https://api.tiingo.com/tiingo/daily/{ticker}/prices",
                           {"startDate": "1980-01-01", "token": token}, validate=validate)
    series = [{"date": p["date"][:10], "value": float(p["adjClose"])} for p in reply if p.get("adjClose")]
    return {"name": ticker.upper(), "source": "Tiingo daily adjClose", "basis": "adjusted close (splits + dividends)",
            "resolution": "daily", "series": series}, path


def compare(main, other):
    """Compare two adjusted series on shared dates, both scaled to 1.0 at their last shared date.
    Returns (max relative difference, date where it happens, number of shared dates)."""
    a = {p["date"]: p["value"] for p in main["series"]}
    b = {p["date"]: p["value"] for p in other["series"]}
    common = sorted(set(a) & set(b))
    if len(common) < 10:
        raise FetchError(f"only {len(common)} shared dates between sources, can't cross-check")
    ra, rb = a[common[-1]], b[common[-1]]
    worst = max(common, key=lambda d: abs((a[d] / ra) / (b[d] / rb) - 1))
    return abs((a[worst] / ra) / (b[worst] / rb) - 1), worst, len(common)


def crypto(symbol):
    reply, path = get_json("alphavantage", "https://www.alphavantage.co/query",
                           {"function": "DIGITAL_CURRENCY_DAILY", "symbol": symbol, "market": "USD",
                            "apikey": env("ALPHA_VANTAGE_API_KEY")}, validate=_av_validate)
    key = next((k for k in reply if "Time Series" in k), None)
    if not key:
        raise FetchError("Alpha Vantage: no crypto series in reply")
    series = []
    for d, v in reply[key].items():
        close = v.get("4. close") or v.get("4a. close (USD)")  # field name changed over time
        if close is None:
            raise FetchError(f"Alpha Vantage crypto: no close field on {d}")
        series.append({"date": d, "value": float(close)})
    series.sort(key=lambda p: p["date"])
    return {"name": symbol.upper(), "source": "Alpha Vantage DIGITAL_CURRENCY_DAILY (USD)",
            "basis": "daily close, one exchange feed: say 'about'", "resolution": "daily", "series": series}, path


def fred(series_id):
    key = env("FRED_API_KEY")

    def validate(reply):
        if "error_message" in reply:
            raise FetchError(f"FRED refused: {reply['error_message'][:120]}")

    meta, p1 = get_json("fred", "https://api.stlouisfed.org/fred/series",
                        {"series_id": series_id, "api_key": key, "file_type": "json"}, validate=validate)
    obs, p2 = get_json("fred", "https://api.stlouisfed.org/fred/series/observations",
                       {"series_id": series_id, "api_key": key, "file_type": "json"}, validate=validate)
    m = meta["seriess"][0]
    # FRED writes "." for a missing value; skip it explicitly (the old code crashed on it silently).
    series = [{"date": o["date"], "value": float(o["value"])} for o in obs["observations"] if o["value"] != "."]
    freq = m.get("frequency_short", "D")
    return {"name": m["title"], "source": f"FRED {series_id}", "units": m.get("units"),
            "seasonal_adjustment": m.get("seasonal_adjustment_short"),
            "basis": f"{m.get('units')} ({m.get('seasonal_adjustment_short')})",
            "resolution": {"D": "daily", "W": "weekly", "M": "monthly"}.get(freq, "monthly"),
            "check": "official source", "series": series}, [p1, p2]


def sec(ticker, concept):
    ua = env("SEC_USER_AGENT")  # SEC requires "Name contact@email" in every request
    headers = {"User-Agent": ua}
    tickers, p1 = get_json("sec", "https://www.sec.gov/files/company_tickers.json", {}, headers=headers, max_age_days=7)
    cik = next((v["cik_str"] for v in tickers.values() if v["ticker"].upper() == ticker.upper()), None)
    if cik is None:
        raise FetchError(f"SEC: ticker {ticker} not found (delisted? → manual check)")
    facts, p2 = get_json("sec", f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", {}, headers=headers)
    node = facts.get("facts", {}).get("us-gaap", {}).get(concept)
    if not node:
        raise FetchError(f"SEC: {ticker} has no us-gaap:{concept}")
    unit, rows = next(iter(node["units"].items()))
    # keep one value per fiscal year: full-year 10-K figures, latest filing wins
    by_year = {}
    for r in rows:
        if r.get("form") == "10-K" and r.get("fp") == "FY" and r.get("frame", "").startswith("CY") and len(r["frame"]) == 6:
            by_year[r["frame"]] = r
    series = sorted(({"date": r["end"], "value": float(r["val"]), "filed": r["filed"], "accn": r["accn"]}
                     for r in by_year.values()), key=lambda p: p["date"])
    if not series:
        raise FetchError(f"SEC: no full-year 10-K values for {concept}")
    return {"name": f"{ticker.upper()} {concept}", "source": f"SEC EDGAR companyfacts us-gaap:{concept}",
            "units": unit, "basis": "annual 10-K, calendar-year frame", "resolution": "yearly",
            "check": "official source (10-K)", "series": series}, [p1, p2]


# ---------- CLI ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prices", "crypto", "fred", "sec"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--source", default="tiingo", choices=["tiingo", "av-weekly", "av-monthly"])
    ap.add_argument("--check", default="av-weekly", choices=["av-weekly", "none"])
    a = ap.parse_args(argv)
    try:
        if a.cmd == "prices":
            ticker, out = a.args[0], a.args[1]
            if a.source == "tiingo":
                data, path = tiingo_daily(ticker)
            else:
                data, path = av_adjusted(ticker, a.source.split("-")[1])
            raws = [path]
            if a.check == "av-weekly" and a.source != "av-weekly":
                other, p2 = av_adjusted(ticker, "weekly")
                diff, worst, n = compare(data, other)
                raws.append(p2)
                data["check"] = f"Alpha Vantage weekly: max diff {diff:.2%} on {worst} over {n} shared dates"
                if diff > CHECK_TOLERANCE:
                    write_out(out, data, raws)
                    raise FetchError(f"sources disagree by {diff:.2%} on {worst} (limit {CHECK_TOLERANCE:.0%}): "
                                     "show the owner before using this data")
            else:
                data["check"] = "not cross-checked"
            write_out(out, data, raws)
        elif a.cmd == "crypto":
            data, path = crypto(a.args[0])
            data["check"] = "single source"
            write_out(a.args[1], data, [path])
        elif a.cmd == "fred":
            data, paths = fred(a.args[0])
            write_out(a.args[1], data, paths)
        else:
            data, paths = sec(a.args[0], a.args[1])
            write_out(a.args[2], data, paths)
    except (FetchError, requests.RequestException, IndexError, KeyError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
