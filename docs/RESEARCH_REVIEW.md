# Research method review (2026-11-09)

> Legacy code referenced below was removed 2026-11-09; restore any file with `git show 3c768e1:YouTubeAutomation/<path>`.

Owner's question: is the old research method (`YouTubeAutomation/agents/research_agent.py` + APIs) good enough for finance, where a wrong number is a real problem? Or should it change?

**Short answer: change it.** The data sources were mostly fine; the code that used them produced wrong numbers, and nothing checked the numbers that ended up in the script.

## 1. What the old method did

1. Gemini split the topic into subject / year / niche.
2. Called APIs in parallel: Alpha Vantage (prices), FRED (economy), Tavily (news context), Serper (Google search).
3. Turned the results into "facts" like *"Amazon price in 2001 was $X"*, marked `confidence: high`.
4. Script agent "locked" those numbers into the script.
5. A "verification agent" (Gemini) reviewed tone and logic. Its prompt says **"DO NOT attempt to verify specific numbers"**, so no number was ever checked.
6. SQLite cache, 30-day expiry.

## 2. Problems found (checked in the code and in the cache file)

| # | Problem | Evidence | Effect |
|---|---|---|---|
| 1 | **Wrong company.** Ticker is guessed: "bitcoin" → BTC, "apple" → AAPL, **everything else → SPY** (S&P 500 fund) | `research_agent.py` `_call_alpha_vantage`; cache holds only SPY prices while topics were Amazon, Enron, Starbucks, BNPL… | Script says "Amazon's price was $X" using the S&P 500 fund's price |
| 2 | **Unadjusted prices.** Reads `4. close` instead of `5. adjusted close` | `_extract_price_for_date` | Any stock that split is wrong by the split factor (NVDA: 40×, AAPL: 224×) |
| 3 | **Errors saved as data.** Alpha Vantage rate-limit replies come back as normal JSON and get cached for 30 days | 2 cached rows: "Thank you for using Alpha Vantage! Please consider spreading out your free API requests…" | Topic silently gets no price, or a later run reuses the error |
| 4 | **Month instead of date.** Uses the month-end close for any date in that month, without saying so | `_extract_price_for_date` | "Bought on Jan 3" priced at Jan 31 |
| 5 | **Silent fallbacks.** If topic parsing fails: "General, 2023". If a FRED date is missing: nearest value up to 30 days away | `_decompose_topic`, `extract_value_for_date` | Wrong year/value with no warning |
| 6 | **ROI period fixed to 1 year**, regardless of the story | `exit_date_str = year + 1` | Return number doesn't match what the script describes |
| 7 | **"Confidence: high" is hard-coded**, not measured | `_validate_data` | False sense of safety |
| 8 | **No check that script numbers come from data.** Number "locking" only checks that numbers survive rewrites, not that they're true | `script_agent.py` | LLM-invented numbers pass |
| 9 | **Search snippets as facts.** Tavily/Serper snippets go into "hooks" with no source rating | `_call_tavily`, `_call_serper` | Old predictions/opinion pieces can become "facts" |

The **research skill** (`.agent/skills/research_agent/SKILL.md`) had the right principles (primary sources, 2+ sources, attribution, exact dates); the code didn't follow them.

## 3. New approach

**Rule: numbers are never written by an LLM or copied from a search snippet. They are fetched and calculated by small, tested scripts from official data, and every number in the script must trace back to one.** Claude decides *what* to look up (exact ticker, exact dates) and writes the story; code produces the numbers.

### 3.1 Where each kind of fact comes from

| Fact type | Primary source | Second source (cross-check) | Notes |
|---|---|---|---|
| US stock / ETF prices | **Tiingo** daily **adjusted** close (free tier; needs a free key) | Alpha Vantage monthly/weekly **adjusted** (key exists; daily adjusted is believed to be paid-only on Alpha Vantage: confirm at build) | Code compares both on overlapping dates; >1% difference = stop and show owner |
| Economy (rates, CPI, unemployment, mortgage, GDP) | **FRED** (St. Louis Fed; key exists) | none needed (official) | Record series ID, units, seasonal adjustment, date |
| Inflation adjustment | FRED `CPIAUCSL` | | Code does the maths; state "in 2026 dollars" |
| Company numbers (revenue, profit, debt, shares) | **SEC EDGAR** company facts API (official, free, no key) | the 10-K filing link | SEC asks for a contact name in requests: owner chooses it |
| Crypto prices | Alpha Vantage digital currency | CoinGecko (free) | Crypto prices differ by exchange: say "about" |
| Delisted companies (Enron, Lehman) | Often missing from free APIs | SEC filings + reputable archives | Marked **manual check** |
| Events, dates, quotes ("Fed raised rates on…", "CEO said…") | Claude web search, **primary or top-tier sources** (SEC, Fed, company IR, Reuters, AP, WSJ, Bloomberg) | a 2nd independent source | URL + date stored for each |

Tavily and Serper: not needed (Claude Code has its own web search). Keys stay in `.env`, unused unless we need them.

### 3.2 Calculations in code, with tests
`engine/tools/finance_calc.py`: "$1,000 invested on date A is worth $X on date B", return %, yearly growth (CAGR), **peak-to-trough drop**, inflation-adjusted value. Each says whether dividends are included. Small tests with known answers (e.g. a known split, a known crash) so a bug can't hide.

### 3.3 `facts.json`: one entry per number
```json
{ "id": "nvda_2022_drop", "say": "59%", "value": -0.593,
  "what": "NVDA peak-to-trough drop, adjusted close",
  "from": "2021-11-29", "to": "2022-10-14",
  "source": "Tiingo daily adjClose", "check": "Alpha Vantage weekly adjusted -0.59 ✓",
  "fetched": "2026-11-12" }
```
`check_plan.py` refuses to render if a number in `script.txt` is missing from `facts.json`.

### 3.4 Cache that can't lie
- Raw API replies saved as files in the run (`data/`), so every video's numbers can be re-checked later.
- Error / rate-limit replies are **never** cached; the script stops with a clear message.
- Data for recent dates is re-fetched; old history can be reused.
- Alpha Vantage free tier ≈ 25 requests/day: the cache matters.

### 3.5 Wording rules (in the niche skill)
Round only the way the fact says (`say`), name the period ("from its 2021 peak to Oct 2022"), say "about" for estimates, no predictions or advice, "not financial advice" in description.

### 3.6 Manual option (owner's check)
Before upload, Claude writes `review/facts_review.md`: each claim, the number, the source link. The owner can open the links and tick them. Any `manual check` facts are listed first.

## 3.7 Re-check of our own test
Style A's `nvda.json` used Alpha Vantage **monthly adjusted** close (correct adjustment). The script's "59% peak-to-trough" will be re-verified with daily data once `finance_calc.py` exists, since monthly closes can understate a drop.

## 4. What to keep from the old project
- FRED series list (FEDFUNDS, DGS10, UNRATE, CPIAUCSL, MORTGAGE30US, …).
- The research skill's principles (rewritten into `video-core/references/data-honesty.md`).
- Idea of a cache (new, file-based, no error caching).
- Everything else in `research_agent.py`, `verification_agent.py` is retired.

## 5. To confirm with owner
1. Sign up for a free **Tiingo** key (daily adjusted prices; Alpha Vantage free tier only gives weekly/monthly adjusted).
2. A contact name/email for SEC EDGAR requests (SEC requires one in the request header; can be a project email).
