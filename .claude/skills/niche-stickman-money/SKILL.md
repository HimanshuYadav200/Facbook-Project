---
name: niche-stickman-money
description: The stickman money-parables niche (calm stickman stories that teach one money lesson to US adults, ~1:30, Facebook first). Use when choosing topics, writing scripts, picking the cast or voice for a stickman-money run, or refining this niche from references in references/stickman-psychology/.
---

# Niche: stickman money parables

Built from `references/stickman-psychology/analysis.md` (viral calm stickman reels). Style: `style-stickman-calm`. Machine rules (length 80–100 s, style, banned phrases) live in `niche.json` next to this file. The sister niche (relationships) will reuse the same style with its own niche skill.

## Who and why
- **Audience:** US adults 25–60 on Facebook, often parents. They share stories that say what they wish they could tell their kid, partner or friend.
- **Promise:** one short story, one money lesson, said in one quotable line.
- **Shares are the goal:** end on the quotable moral, then a soft line that makes the viewer think of a specific person ("Somewhere, someone just got their first paycheck."). Do **not** say "share this / send this / tag" in the narration: Meta demotes engagement bait. The comment question goes in the caption.

## Defaults
| Setting | Value |
|---|---|
| Voice | `af_kore`, speed 0.9, `--sentence-gap 0.45` (owner's pick, 2026-11-10) → ~175 wpm |
| Script length | 230–260 words → 80–100 s |
| Shots | ~22, one image per sentence or two |
| Music | `the-end-soundaudio`, volume 0.08 (non-copyright, owner) |

## Script formulas (pick one)
1. **Two people, same start** (best first): same job / same pay / same gift → different choices → a test (job loss, emergency, years later) → the wise one explains → moral line → share line.
2. **Parent and child lesson**: a parent sets a small test ($100 to spend, earn $10) → the child learns the value → general lesson.
3. **"Your parents' money" truth**: second person, list, turn, gentle call to act.
4. **Stages / signs** ("4 stages of a money habit"): number promised in the hook, each stage named + 2–3 relatable lines.

## Script rules
- **Hook in the first sentence**: a situation with a built-in comparison or surprise ("Two brothers got their first job on the same day…").
- Simple words, short sentences; sentences end often (the sentence gap makes the calm rhythm).
- **Numbers:** story numbers are fine but must be digits and added to `facts.json` as `"kind": "illustrative"`; spelled small counts ("two weeks") are fine. Any real statistic needs a source via the finance tools (`video-core/references/data-honesty.md`). No invented science or "studies show".
- No advice to buy or sell anything; banned phrases in `niche.json`.
- **Cast:** pick 2–4 characters, give each one clothing identifier, keep it in every image prompt. Characters change from story to story (like the reference page).

## Upload text
Write `upload.md` per run following `video-core/references/upload-policy.md` (example: `runs/stickman-money/2026-11-10_two-brothers-paycheck/upload.md`). Base tags: money lesson, saving money, personal finance for beginners, financial literacy, moral story, life lesson, stickman story + 4–6 story-specific ones.
US audience: follow `upload-policy.md` §4 (Post at slot, English (US) settings, US words).
Base hashtags (pick 3–4): #MoneyLessons #PersonalFinance #MoneyMindset #FinancialLiteracy #LifeLessons; rotate by story: #SavingMoney #EmergencyFund #PayYourselfFirst · #Parenting #RaisingKids #FamilyValues · #LifestyleCreep #CareerAdvice · #StickmanStory #MoralStory · #AmericanDream #MiddleClass (only when they fit).

## Facebook Page
- Name: owner's pick (suggested: Little Money Lessons, Quiet Money Stories, The Money Parables, Small Coins, Big Lessons).
- Categories (max 3): **Digital creator**, **Education**, **Personal blog**. Not "Financial Service".
- Bio (≤ 101 chars): "One short story. One money lesson. For anyone who wants to spend smarter and worry less. 🇺🇸"

## Topic bank
`references/topics.md`: 100 seeds (formula, inspiration, who to share with, whether a real stat fits). Mark each used with the run id; don't run the same formula 3 times in a row. Seeds are shapes, never text to copy.
Free sources when the bank runs low: Project Gutenberg fables (Aesop, Panchatantra, Jataka, Tolstoy, Nasreddin; public domain), OpenStax *Psychology 2e* (CC BY) for the psychology behind a story, US government data (Fed SHED survey, FRED, BLS) for real stats via `fetch_data.py`. No paid API needed.
