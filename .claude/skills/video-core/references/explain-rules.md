# Explain, don't decorate

Monetization depends on real value: the video must explain something a slideshow can't.
(Ideas adapted from the OpenChatCut explainer skill, written in our own words; see `docs/OPENCHATCUT_SKILL_ANALYSIS.md`.)

## The explanation test
For every teaching beat, finish the sentence and put it in the shot's `teach` field:
> "The viewer understands ___ because the screen shows ___ changing / relating to ___."
If you can't fill it precisely, the shot is decoration. Style motion (wobble, shake, fast cuts, film grain) is fine everywhere, but it can't be the only thing on a teaching beat.

## Claim → visual (finance)
| Claim in the script | Visual | Must be on screen |
|---|---|---|
| Value over time ("$1,000 became …") | line chart drawing in + $ counter | amount, start date, scale (log/linear), source |
| A crash / drop | line falling from peak to trough, red | the % and the two dates |
| A vs B | two lines or bars on **one shared axis** | same start amount, same dates |
| Compounding | growing stack / counter with years ticking | years, final amount |
| Cost of a habit | counter adding per day → month → year | the unit and the period |
| Inflation | same item, two prices, two years | "in YYYY dollars" |
| A mechanism (how a margin call works) | 3–5 labelled things, one change per beat | what changed, why, result |

## Pacing a teaching beat
1. Introduce the thing before animating it (title, then line).
2. One change per beat; the change lands on the spoken word it explains, never before.
3. Hold the result long enough to read (≥ 1 s after the number appears).
4. At most 3–5 labels on screen; same words on screen as in narration.
5. Captions are short labels or numbers, never full sentences.

## Honest charts
Units and dates visible, same scale for comparisons, no smoothing that hides a drop, no invented in-between values, log scale labelled.
