---
name: niche-skulsy-finance
description: The Skulsy USA-finance niche (cartoon skeleton Skulsy, personal finance and investing stories with real data, for Facebook then YouTube). Use when choosing topics, writing scripts, picking voice/style, or refining this niche from references in references/skulsy-finance/.
---

# Niche: Skulsy + USA finance

## Who and why
- **Audience:** US adults 25–55 on Facebook (then YouTube) who like money stories but aren't finance experts.
- **Promise:** a true money story told through Skulsy, with real numbers, so the viewer understands one idea (compounding, panic selling, inflation, fees, a famous crash…).
- **Skulsy:** friendly cartoon skeleton, round white skull, big dark eye sockets, wide grin; brown three-piece suit, green tie, grey bowler hat (vintage) / hoodie rig (flat). He's an everyman: sometimes smart, often makes the mistake viewers recognise. Deadpan, never mean.
- **Monetization rule:** every video must teach something with real data; no slideshow of AI images over generic narration.

## Defaults
Machine rules (length 120–168 s, styles, banned phrases) live in `niche.json` next to this file; new runs copy it.

| Setting | vintage-story | flat-fastcut |
|---|---|---|
| Voice (Kokoro) | `bm_george`, speed 0.95 | `am_puck`, speed 1.1 |
| Script length for 2:00–2:48 | 240–335 words | 390–550 words |
| Best for | history, "what if you'd invested", famous companies | habits, mistakes, behaviour (panic selling, over-trading, lifestyle creep) |
Other voices: audition with care, the owner wants to try more (open item).

## Script rules
1. **Pick a pattern** from `references/script-patterns.md`; build the facts **before** writing.
2. **Numbers:** digits only, every one from `facts.json` (`video-core/references/data-honesty.md`). Dollars invested, not share prices. Name dates and periods.
3. **Hook (first 3 s, ≤ 12 words):** a specific situation or number. "January 2016. Skulsy put $1,000 into a company that made graphics cards."
4. **Time anchors:** 3+ dates/years so the story moves ("By the end of 2020…", "A year later?").
5. **One idea.** Everything serves one takeaway, said in one plain line near the end ("He just sat still.").
6. **No advice or predictions.** Tell what happened, not what to buy. Banned: guaranteed, risk-free, can't lose, buy now, will go up, get rich quick (full list in this skill's `niche.json`; check_plan refuses them).
7. **Sound human:** `references/writing-style.md`.
8. **Pronunciation:** "A I" not "AI"; "262 times" not "262x"; check names in voice.py's match % and listen.

## Topic ideas (each needs real data)
$1,000 in a famous stock at a famous moment (and the drawdowns on the way) · the cost of panic-selling in 2008 / 2020 · inflation: what $100 from 2000 buys today · a fee of 1% over 30 years · credit-card minimum payments · S&P 500 vs "safe" savings since 2010 · mortgage rates 2021 vs 2023 on the same house · lifestyle creep with a raise.

## Refining this niche
Owner adds screenshots / reels / notes to `references/skulsy-finance/` → Claude measures, writes `analysis.md`, proposes skill changes, applies after OK, logs in `docs/CONTEXT.md` (see `references/README.md`).
