"""Check a run's facts on the web with Tavily, so the owner doesn't have to open every source by hand.

Usage: engine/.venv/bin/python engine/tools/fact_check.py runs/<niche>/<id> [--all] [--apply]
  default: only facts marked "check": "manual ..." (the ones the owner had to tick by hand)
  --all:   every fact except illustrative (story-only) ones
  --apply: facts confirmed by 2+ independent sites lose their manual mark in facts.json
           (backup facts.json.bak-<time> first; the old note is kept as "check_was")
Writes review/fact_check.md (verdict + sources per fact). One Tavily credit per fact (free tier: 1,000/month);
answers are cached in engine/cache/tavily/ for 30 days, so re-runs cost nothing.

Better checks: give each fact a short "search" query ("Victor Lustig Al Capone $5,000") and, for text facts,
"key": 2-3 terms a page must contain to back it (["Capone", "Lustig", "5,000"]). Without them the tool builds a
query from the names and numbers in the fact and needs 70% of the fact's words on a page (strict: long sentences fail).
Verdicts:
  CONFIRMED  - the fact's number (or, for text facts, most of its key words) is on 2+ independent sites
  ONE SITE   - found on only one site: weak, read it
  NOT FOUND  - no result has it: the claim may be wrong, or worded differently; read the sources
Keys: TAVILY_API_KEY in .env (TAVILY_API_KEY_BACKUP is tried when the first is out of credits). Never printed.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from check_plan import parse_numbers
from fetch_data import CACHE, FetchError, env

URL = "https://api.tavily.com/search"
STOP = set("the a an and or of to in on for with that this was were is are be by as at from it its their they "
           "them his her he she so but not than then into about after before over very really do does did".split())


def search(query):
    """Tavily search (basic depth = 1 credit), cached. Raises FetchError on any bad reply."""
    path = CACHE / "tavily" / (hashlib.sha1(query.encode()).hexdigest()[:16] + ".json")
    if path.exists() and time.time() - path.stat().st_mtime < 30 * 86400:
        return json.loads(path.read_text())
    # full page text: the short snippet often cuts off before the number
    body = {"query": query, "search_depth": "basic", "max_results": 6, "include_answer": True,
            "include_raw_content": "text"}
    for name in ("TAVILY_API_KEY", "TAVILY_API_KEY_BACKUP"):
        key = env(name, required=name == "TAVILY_API_KEY")
        if not key:
            continue
        r = requests.post(URL, json=body, headers={"Authorization": f"Bearer {key}"}, timeout=60)
        if r.status_code in (401, 429, 432, 433):  # bad key / rate or credit limit: try the backup key
            print(f"  {name}: HTTP {r.status_code}, trying the next key", file=sys.stderr)
            continue
        if r.status_code != 200:
            raise FetchError(f"tavily: HTTP {r.status_code}")
        reply = r.json()
        if not isinstance(reply.get("results"), list):
            raise FetchError("tavily: reply has no results list")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reply))
        return reply
    raise FetchError("tavily: no working key (out of credits?)")


def site(url):
    # shortcut: last two labels of the host ("bbc.co.uk" -> "co.uk"); fine for counting distinct sites
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return ".".join(host.split(".")[-2:])


def key_words(text):
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP}


def supports(fact, text):
    """Does this page text back the fact? `key` terms (if given) must all appear; numbers in `say` must all
    appear (within 0.5%); text facts without `key`: at least 70% of the key words of `say` appear."""
    keys = fact.get("key") or []
    if keys and not all(k.lower() in text.lower() for k in keys):
        return False
    want = [(u, v) for _, u, v in parse_numbers(fact["say"])]
    if want:
        have = [v for _, _, v in parse_numbers(text)]
        return all(any(abs(v - h) <= 0.005 * max(abs(v), 1) for h in have) for _, v in want)
    if keys:
        return True
    words = key_words(fact["say"])
    return bool(words) and len(words & key_words(text)) >= 0.7 * len(words)


def query_for(fact):
    """A short keyword query: the fact's "search" field if Claude wrote one (best), else names and numbers
    from what + say. Whole sentences as queries brought back junk (tested 2026-11-11)."""
    if fact.get("search"):
        return str(fact["search"])[:390]
    text = f"{fact.get('what', '')} {fact['say']}"
    names = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*", text)
    nums = [raw for raw, _, _ in parse_numbers(fact["say"])]
    terms = []
    for t in names + nums + sorted(key_words(fact["say"]), key=len, reverse=True):
        if t.lower() not in STOP and t.lower() not in {x.lower() for x in terms}:
            terms.append(t)
    return " ".join(terms[:10])


def judge(fact, reply):
    sites = {}
    for res in reply["results"]:
        if supports(fact, f"{res.get('title', '')} {res.get('content', '')} {res.get('raw_content') or ''}"):
            sites.setdefault(site(res["url"]), res["url"])
    verdict = "CONFIRMED" if len(sites) >= 2 else "ONE SITE" if sites else "NOT FOUND"
    return verdict, sites


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    run = Path(a.run)
    facts = json.loads((run / "facts.json").read_text())
    if not isinstance(facts, list):
        print("ERROR: facts.json must be a list", file=sys.stderr)
        return 1
    todo = [f for f in facts if f.get("kind") != "illustrative" and f.get("say")
            and (a.all or "manual" in str(f.get("check", "")).lower())]
    print(f"{len(todo)} fact(s) to check (up to {len(todo)} Tavily credits; cached answers are free)")

    rows, confirmed = [], set()
    for f in todo:
        try:
            reply = search(query_for(f))
        except FetchError as e:
            print(f"ERROR: {f['id']}: {e}", file=sys.stderr)
            return 1
        verdict, sites = judge(f, reply)
        if verdict == "CONFIRMED":
            confirmed.add(f["id"])
        print(f"{verdict:10} {f['id']}: {', '.join(sites) or '-'}")
        found = "<br>".join(f"[{s}]({u})" for s, u in sites.items()) or "–"
        answer = (reply.get("answer") or "").replace("|", "/").replace("\n", " ")[:300]
        rows.append(f"| {verdict} | {f['id']} | {f['say']} | {found} | {answer} |")

    out = run / "review" / "fact_check.md"
    out.parent.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    out.write_text("\n".join([
        f"# Fact check (Tavily): {run.name}", "",
        f"{today}. CONFIRMED = on 2+ independent sites. Read ONE SITE / NOT FOUND rows before upload.", "",
        "| verdict | id | video says | sites that back it | search engine's summary (not proof) |",
        "|---|---|---|---|---|", *rows, ""]))
    print(f"-> {out}")

    if a.apply and confirmed:
        changed = [f for f in facts if f.get("id") in confirmed and "manual" in str(f.get("check", "")).lower()]
        if changed:
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy(run / "facts.json", run / f"facts.json.bak-{stamp}")
            for f in changed:
                f["check_was"] = f["check"]
                f["check"] = f"auto-confirmed {today} by fact_check.py (2+ sites, see review/fact_check.md)"
            (run / "facts.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False) + "\n")
            print(f"facts.json: {len(changed)} manual mark(s) cleared (backup facts.json.bak-{stamp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
