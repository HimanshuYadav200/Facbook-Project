"""Finance maths for scripts: every number a video says comes out of here, with its dates and source.

Input is a data file written by fetch_data.py:
  {"name", "source", "basis", "resolution", "series": [{"date": "YYYY-MM-DD", "value": float}, ...]}

Commands (each prints one facts.json entry; add --id to name it):
  invest   <data.json> <amount> <start> <end>    "$1,000 on start is worth $X on end"
  change   <data.json> <start> <end>             % change between two dates
  drawdown <data.json> <start> <end>             biggest peak-to-trough drop inside the window
  cagr     <data.json> <start> <end>             yearly growth rate
  inflate  <cpi.json> <amount> <from> <to>       amount in `to` dollars (CPI)

Dates: if a date has no data (weekend, holiday) the last value ON OR BEFORE it is used, and the
real date is written into the fact. More than MAX_GAP_DAYS without data is an error, never a guess.
"""
import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

MAX_GAP_DAYS = {"daily": 7, "weekly": 10, "monthly": 35}


class DataError(Exception):
    pass


def load(path):
    d = json.loads(Path(path).read_text())
    s = d.get("series") or []
    if not s:
        raise DataError(f"{path}: empty series")
    dates = [p["date"] for p in s]
    if dates != sorted(dates):
        raise DataError(f"{path}: series not sorted by date")
    for p in s:
        if not isinstance(p["value"], (int, float)) or math.isnan(p["value"]) or p["value"] <= 0:
            raise DataError(f"{path}: bad value {p['value']!r} on {p['date']}")
    d["_path"] = str(path)
    return d


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def point_on(data, day):
    """Last data point on or before `day`. Raises if the nearest one is too old."""
    series = data["series"]
    if day < series[0]["date"]:
        raise DataError(f"{day} is before the data starts ({series[0]['date']})")
    best = None
    for p in series:
        if p["date"] <= day:
            best = p
        else:
            break
    gap = (_d(day) - _d(best["date"])).days
    limit = MAX_GAP_DAYS.get(data.get("resolution", "daily"), 7)
    if gap > limit:
        raise DataError(f"no data within {limit} days before {day} (nearest {best['date']})")
    return best


def window(data, start, end):
    pts = [p for p in data["series"] if start <= p["date"] <= end]
    if len(pts) < 2:
        raise DataError(f"fewer than 2 data points between {start} and {end}")
    return pts


# ---------- calculations (pure, tested in engine/tests/test_finance_calc.py) ----------

def invest(data, amount, start, end):
    a, b = point_on(data, start), point_on(data, end)
    value = amount * b["value"] / a["value"]
    return {"start": a, "end": b, "amount": amount, "value": value,
            "change": value / amount - 1, "multiple": value / amount}


def change(data, start, end):
    a, b = point_on(data, start), point_on(data, end)
    return {"start": a, "end": b, "change": b["value"] / a["value"] - 1}


def drawdown(data, start, end):
    """Largest fall from a running peak to a later low, inside [start, end]."""
    pts = window(data, start, end)
    peak, best = pts[0], None
    for p in pts[1:]:
        if p["value"] > peak["value"]:
            peak = p
        dd = p["value"] / peak["value"] - 1
        if best is None or dd < best["change"]:
            best = {"peak": peak, "trough": p, "change": dd}
    if best["change"] >= 0:
        raise DataError(f"no drop between {start} and {end}")
    return best


def cagr(data, start, end):
    a, b = point_on(data, start), point_on(data, end)
    years = (_d(b["date"]) - _d(a["date"])).days / 365.25
    if years < 1:
        raise DataError("CAGR needs at least 1 year; use `change` instead")
    return {"start": a, "end": b, "years": years, "cagr": (b["value"] / a["value"]) ** (1 / years) - 1}


def inflate(cpi, amount, frm, to):
    a, b = point_on(cpi, frm), point_on(cpi, to)
    return {"start": a, "end": b, "amount": amount, "value": amount * b["value"] / a["value"]}


# ---------- how numbers are said on screen / in narration ----------

def say_dollars(v):
    """3 significant figures, so we never claim fake precision: 13912.4 -> $13,900."""
    if v <= 0:
        raise ValueError("dollar amount must be positive")
    digits = 3 - int(math.floor(math.log10(v))) - 1
    r = round(v, digits)
    return f"${r:,.0f}" if r >= 100 else f"${r:,.2f}"


def say_pct(x):
    """Whole percent, sign shown by the words in the script, not here: -0.5934 -> 59%."""
    return f"{abs(x) * 100:.0f}%"


def say_multiple(m):
    return f"{m:.0f}x" if m >= 10 else f"{m:.1f}x"


# ---------- CLI: turn a calculation into a facts.json entry ----------

def _fact(args, data, what, say, value, period, extra=None):
    f = {
        "id": args.id or args.cmd,
        "say": say,
        "value": round(value, 6),
        "what": what,
        "period": period,
        "basis": data.get("basis", ""),
        "source": data.get("source", ""),
        "data_file": data["_path"],
        "check": data.get("check", "not cross-checked"),
        "computed": date.today().isoformat(),
    }
    if extra:
        f.update(extra)
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["invest", "change", "drawdown", "cagr", "inflate"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--id", help="fact id for facts.json")
    a = ap.parse_args(argv)
    usage = {"invest": "<data.json> <amount> <start> <end>", "change": "<data.json> <start> <end>",
             "drawdown": "<data.json> <start> <end>", "cagr": "<data.json> <start> <end>",
             "inflate": "<cpi.json> <amount> <from> <to>"}[a.cmd]
    if len(a.args) != len(usage.split()):
        print(f"ERROR: {a.cmd} needs {usage}", file=sys.stderr)
        return 2
    try:
        data = load(a.args[0])
        name = data.get("name", "")
        if a.cmd == "invest":
            amount, s, e = float(a.args[1]), a.args[2], a.args[3]
            r = invest(data, amount, s, e)
            fact = _fact(a, data, f"{say_dollars(amount)} in {name} on {r['start']['date']} worth on {r['end']['date']}",
                         say_dollars(r["value"]), r["value"], [r["start"]["date"], r["end"]["date"]],
                         {"also": {"amount": say_dollars(amount), "change": say_pct(r["change"]), "multiple": say_multiple(r["multiple"])}})
        elif a.cmd == "change":
            r = change(data, a.args[1], a.args[2])
            word = "rise" if r["change"] > 0 else "fall"
            fact = _fact(a, data, f"{name} {word} {r['start']['date']} to {r['end']['date']}",
                         say_pct(r["change"]), r["change"], [r["start"]["date"], r["end"]["date"]])
        elif a.cmd == "drawdown":
            r = drawdown(data, a.args[1], a.args[2])
            fact = _fact(a, data, f"{name} peak-to-trough drop, peak {r['peak']['date']}, trough {r['trough']['date']}",
                         say_pct(r["change"]), r["change"], [r["peak"]["date"], r["trough"]["date"]])
        elif a.cmd == "cagr":
            r = cagr(data, a.args[1], a.args[2])
            fact = _fact(a, data, f"{name} yearly growth (CAGR) over {r['years']:.1f} years",
                         say_pct(r["cagr"]), r["cagr"], [r["start"]["date"], r["end"]["date"]])
        else:  # inflate
            amount = float(a.args[1])
            r = inflate(data, amount, a.args[2], a.args[3])
            fact = _fact(a, data, f"{say_dollars(amount)} in {r['start']['date'][:7]} money, in {r['end']['date'][:7]} money (CPI)",
                         say_dollars(r["value"]), r["value"], [r["start"]["date"], r["end"]["date"]])
    except (DataError, ValueError, IndexError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps(fact, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
