---
name: niche-strange-money
description: The strange-money niche (fast, excited animated explainers of TRUE strange money stories, scams and loopholes, 45-70 s, YouTube + Facebook). Use when choosing topics, researching facts, writing scripts or picking the voice for a strange-money run, or refining this niche from references in references/Ricks-clips/.
---

# Niche: strange money (true stories, scams, loopholes)

Built from `references/Ricks-clips/analysis.md` (viral animated explainer shorts). Style: `style-explainer-fast`. Machine rules (length 45–70 s, style, banned phrases) live in `niche.json` next to this file.

## Who and why
- **Audience:** curious adults 18–45 on YouTube Shorts and Facebook Reels. They share "wait, that's real?" moments.
- **Promise:** one true, strange money story, and *how* it worked, in under a minute.
- **True only.** The reference channel sometimes tells fiction as fact; we never do. Every claim has a source in `facts.json` (even when it has no number), listed in the description. Where sources disagree (amounts, counts, dates), say it vaguely ("a fortune", "the biggest dealers in Paris") or pick the most-cited and note it.

## Defaults
| Setting | Value |
|---|---|
| Voice | `am_puck`, speed **1.05**, `--sentence-gap 0.2` → ~185 wpm (owner 2026-11-12: 1.15 was too fast; first used in lucas-toy-rights; older auditions in `references/Ricks-clips/voice-auditions/`, `am_echo` is the runner-up) |
| Script length | 170–200 words → 55–65 s at the slower voice (230 words would run ~75 s, over the 70 s limit) |
| Shots | a new picture every ~1.5–2 s → ~30–35 shots |
| Music | very low or none (reference: almost inaudible) |

## Script formula (all reference reels use it)
1. **Hook = the strange act, stated flatly** in one sentence: "In 1925, a man sold the Eiffel Tower." No question, no "did you know".
2. **"You see,"** + 1–2 lines of context: the stakes.
3. **Doubt / mockery:** someone laughs or refuses; one short quoted line.
4. **Escalation with time markers:** "The next day…", "Weeks later…", "Then one night…".
5. **Payoff:** it worked (or blew up), usually costing or making a lot of money.
6. **Mechanism in 1–2 sentences:** *why* it worked. This is the "aha" people share.
7. Stop on the reveal or a short ironic line. No moral, no call to action, no "follow for more" (engagement bait).

## Script rules
- Short sentences, spoken style, second person sometimes ("You'd think…").
- **Numbers:** digits only, each one in `facts.json` with a source (years are exempt in check_plan, but must still be true).
- Banned phrases in `niche.json` (no advice, no promises). Scams are told as warnings, never as how-tos with steps to copy.
- No real living private people by name; public historical figures are fine.
- Don't copy the reference channel's topics or lines.

## Upload text
`upload.md` per run following `video-core/references/upload-policy.md`. Add a **"Sources:"** line in the description. Base tags: strange history, money facts, true story, scam history, how it worked, animated explainer + 4–6 story-specific ones.
US audience: follow `upload-policy.md` §4 (Post at slot, English (US) settings, US words; prefer US-linked stories in the first week where the order allows).
Base hashtags (pick 3): #TrueStory #History #MoneyFacts #Scam #ConArtist + 1–2 story-specific (#AmericanHistory when it is a US story).
Facebook Page categories (max 3): **Digital creator**, **Education**, **Entertainment website**. Not "Financial Service".

## Facebook Page
- Name: owner's pick (suggested: Strange Money Stories, Money Gone Weird, The Money Oddities, Weird Money Files, True Money Tales).
- Bio (≤ 101 chars): "True money stories so strange they sound fake. Scams, loopholes and wild deals, explained fast. 🇺🇸"
- Reply to comments as the Page, not the personal profile.

## Topic bank
`references/topics.md`. Mark each used with the run id.
