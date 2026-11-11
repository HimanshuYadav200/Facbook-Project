# Data honesty (finance: a wrong number is a real problem)

Background and the old system's failures: `docs/RESEARCH_REVIEW.md`.

## The rule
A number may appear in a script or on screen **only** if it is a `say` (or `also`) value of an entry in the run's `facts.json`. Years are the only exception. `check_plan.py` refuses anything else.

## Where facts come from
| Kind | Tool | Source |
|---|---|---|
| Stock / ETF price history | `fetch_data.py prices` | Tiingo daily adjusted (needs `TIINGO_API_KEY`), cross-checked with Alpha Vantage weekly adjusted. Without Tiingo: `--source av-weekly --check none` and say "weekly close" |
| Economy | `fetch_data.py fred <SERIES>` | FRED (CPIAUCSL, FEDFUNDS, DGS10, UNRATE, MORTGAGE30US, HOUST, CSUSHPISA, GDP) |
| Company figures | `fetch_data.py sec <TICKER> <Concept>` | SEC EDGAR 10-K (needs `SEC_USER_AGENT` = "Name email") |
| Crypto | `fetch_data.py crypto <SYM>` | Alpha Vantage; one feed → say "about" |
| Events, dates, quotes | Claude web search | primary or top-tier source (SEC, Fed, company IR, Reuters, AP, WSJ, Bloomberg) **+ a second independent source**; put both URLs in the fact |
| Delisted companies, anything without an API | manual | fact gets `"check": "manual check"`; listed first in `facts_review.md` |
| Story-only numbers (Skulsy's own made-up money) | none | `"kind": "illustrative"`. **Never** for market data |

## Calculations
Only through `finance_calc.py` (tested): `invest`, `change`, `drawdown`, `cagr`, `inflate`. It prints a ready `facts.json` entry with dates, basis and source. If a date has no data it uses the last value on or before it and says which date; big gaps are errors.

## How to say numbers
- Use the fact's `say` exactly (3 significant figures for $, whole % ). Qualitative wording ("more than half") is fine if it's true for the fact; note it in the fact.
- Talk in **dollars invested**, not share prices: share prices change meaning with every split ("Amazon at $5 in 2001" is a pre-split price).
- Name the period: "from its late-2021 peak to October 2022". Name the basis when it matters: "with dividends reinvested", "in today's dollars".
- Monthly or weekly data hides daily highs/lows: drops look smaller (our test said 59% from monthly data; weekly shows 66%). Use daily data for peak-to-trough claims when available.
- No predictions, no advice, no hype ("guaranteed", "can't lose", "buy now", "will go up" → refused by check_plan). Description ends with "Not financial advice."

## Before upload
1. **Auto check:** give each sourced fact a short `"search"` query and, for text facts, `"key"`: 2–3 terms a page must contain (`["Capone", "Lustig", "5,000"]`). Pick keys that prove the claim, not just the topic. Then `P engine/tools/fact_check.py runs/<niche>/<id> --all --apply` (~1 Tavily credit per fact, cached 30 days). CONFIRMED = found on 2+ independent sites; `--apply` clears their manual marks.
2. ONE SITE / NOT FOUND facts: try a better `search`/`key` once; if still weak, reword the script to what sources do say ("the bank says…") or keep the manual mark for the owner.
3. `review/facts_review.md`: table of every claim → number → source link → data file, manual-check facts first; `review/fact_check.md` next to it.
