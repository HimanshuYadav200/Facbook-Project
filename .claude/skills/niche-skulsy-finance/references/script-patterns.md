# Script patterns (2:00–2:48)

Rewritten from the legacy patterns (`archive/legacy_agent_skills/script_patterns/`). Changes from the legacy versions:
- built for 2:00–2:48, not 45 s;
- no example numbers to copy (the old examples used unadjusted prices, e.g. "Amazon at $5 in 2001", which is wrong after splits): every number comes from facts.json;
- single narrator (no character dialogue / lip-sync);
- no hard-coded "exact" fake precision ("$47,329"): use facts' `say` rounding.

## Shared shape (seconds for a ~2:30 video)
| Part | Time | Job |
|---|---|---|
| Hook | 0–5 | specific situation or number; raises a question |
| Setup | 5–25 | who, when, how much; why it seemed smart / dumb then |
| Build | 25–95 | 3–5 time anchors, stakes rising, a surprise every ~10 s (a drop, an ironic date, a scale jump) |
| Turn | 95–130 | the twist or the hard moment (crash, temptation, the mistake) |
| Payoff | 130–150 | answer the hook with the biggest true number |
| Lesson | last 5–8 | one plain line; then end card |

## Patterns
**What if** — "January 2016. Skulsy put $1,000 into…". Facts: `invest` at 3–4 dates, `drawdown` for the scary part. Turn = the crash he had to sit through. Lesson = patience / time in market.

**The mistake** — Skulsy makes a recognisable error (panic-sold in March 2020, bought the top, paid minimums). Facts: what he got vs what he'd have had (`invest` both paths). Lesson = the habit, not the hindsight.

**The success** — Skulsy does the boring right thing while everyone mocks him. Facts: his path vs the "exciting" path on one shared axis. Optional twist: he almost ruins it.

**Comparison** — two choices, same amount, same dates (S&P 500 vs savings; rent vs buy; lump sum vs monthly). Facts: both paths from the same start. Visual: one shared-axis chart. Verdict + the condition that would flip it.

**Timeline** — 3–5 decisions over 10–20 years, each changing the next. Facts per decision. Payoff = the total.

**Explainer** — Skulsy doesn't understand a concept (compound interest, inflation, expense ratios) and learns it through his own money. Facts: one real-data demonstration (`inflate`, `cagr`). Visual: mechanism with 3–5 labelled parts.

**Reaction (news)** — a recent event (Fed decision, a crash). Needs **today's** data and 2 sources for the event; say the date. Avoid predictions: explain what it means for a normal person, using a past example as the comparison.

**Parable** — Skulsy solves a small-business or money problem in steps (narrated, no dialogue voices). Numbers are illustrative (`"kind": "illustrative"`), but the arithmetic must be correct and shown; label it as an example on screen if it could be mistaken for real data.
