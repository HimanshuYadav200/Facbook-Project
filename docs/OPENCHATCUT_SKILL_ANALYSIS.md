# OpenChatCut "explainer-video" skill: analysis (2026-11-09)

Owner's request: study the skill **without installing it**. The files were downloaded from GitHub as plain text into a temporary folder and read. Nothing was installed or run.

- Repo: `0xsline/OpenChatCut` (≈3k stars, created Jul 2026, last push 2026-11-06). An open-source, local AI video editor with a timeline, Agent Skills, MCP and **Remotion** rendering (same renderer as ours).
- Skill path: `src/agent/skills/explainer-video/`
- Licence: repo is **AGPL-3.0**; the skills folder says it is adapted from `ChatCut-Inc/agent-plugin`, licence **GPL-3.0-only**.

## (a) How the skill is built

**Only two Markdown files. No scripts, no assets, no templates, no code.**

| File | Size | What's in it |
|---|---|---|
| `SKILL.md` | 11 KB | A 16-step workflow, a list of "do not" rules, and a plan format |
| `references/explainer-animation.md` | 9 KB | How to make animation that explains (loaded only when a section uses motion graphics) |

### SKILL.md: the workflow
1. **Classify the job** with fixed labels: where the user starts (topic only / script / voiceover / data …), narration mode (TTS / existing voiceover / none), visual mode (motion graphics / stock / generated / mixed).
2. **Gates** = checkpoints that must be passed before going on:
   - *Animation reference gate*: read the animation reference before planning any motion graphics.
   - *Visual direction gate*: style must be confirmed (a preset chosen from visual cards in their app, or a user reference) before final graphics.
   - *Voice gate*: the user must confirm a voice (audition widget) before any TTS.
3. **Plan** per section: what the viewer will understand, narration text, visual goal, visual treatment, assets, "sync risk".
4. **Timing from real audio**: make the voice first, measure its real length, then make the matching graphics. Never time graphics from a script estimate.
5. **Build one hard section first**, check it, then batch the rest.
6. **QA**: narration-to-visual sync check per section, then a final check (facts, captions, audio mix, export).

Rules worth noting: explain the idea, don't decorate; don't invent facts/prices; no full spoken sentences on screen; don't use unrelated footage as filler.

### explainer-animation.md: the useful part
- **Explanation test**: for every motion, finish the sentence *"The viewer understands ___ because the animation shows ___ changing or relating to ___."* If you can't, the motion is decoration.
- **Claim → visual table**: sequence → step flow; cause/effect → arrow flow; before/after → same frame, same scale; comparison → shared axis; trend → honest chart with unit, baseline, time range; cycle → loop.
- **Diagram states**: start state → one change per beat → result state; keep unchanged things in place; introduce a thing before animating it.
- **Density**: one main point per frame, about 3–5 labelled items max.
- **Honest data**: units, baseline, same scale for comparisons, no fake precision, no filled-in missing data.
- **Transitions with meaning**: morph only if it's the same object; cut when topic/time changes.
- **Sync QA checklist**: things appear before they act, changes land on the spoken word, final state holds long enough to read.

### What it depends on (why installing it alone would not work well)
It is written for the OpenChatCut app, not for plain Claude Code. It calls for:
- other skills not included: `create-motion-graphics` (30 KB), `voice`, `widget-forms`;
- app tools we don't have: `submit_voice`, the timeline editor, the "Design Style" preset catalog with visual cards.

Installed on its own, about half of its steps would point at things that don't exist here.

## (b) Compared with our Style A / Style B approach

| Topic | OpenChatCut skill | Ours (experiments) |
|---|---|---|
| What it is | A **process checklist**, any topic, any look | A **production recipe**: fixed look, real code, real commands |
| Renderer | Remotion behind their app's timeline | Remotion directly, our own components |
| Timing | Per **section**, from real audio duration | Per **word** (`plan.json` shots anchored to word indexes from Whisper), so finer |
| Style | Chosen per video from presets | Locked per style, measured from reference reels |
| Characters | None | Skulsy SVG rig / fixed images |
| Facts | "Don't invent facts" (rule only) | Real Alpha Vantage data, script corrected to match |
| Audio | Music + narration mentioned | Kokoro voice, SFX on cuts, −14 LUFS |
| QA | Written checklist per section | Claude looks at a contact sheet; no written checklist yet |
| User questions | Many confirmations per video (voice, style, plan) | Decided once per style; suited to ~3 videos/day |

**Where we already agree:** time visuals from real audio, short on-screen text, no invented facts, review before done.

**What they have that we lack:**
1. The **explanation test** and the **claim → visual table**. This is the clearest way to make our videos "value add" rather than an AI slideshow (matters for monetization).
2. Honest-chart rules written down (units, baseline, same scale).
3. A written **sync QA checklist** (we review by eye, without a list).
4. "Build the hardest section first, then batch".

**Where it does not fit us:**
- It treats quick decorative motion as suspect. Style B's wobble/shake every ~0.8 s *is* the style (retention). For us the rule should be: style motion is allowed everywhere, but **every data/teaching beat must pass the explanation test**.
- Its many per-video confirmations are too slow for 3 videos/day.
- It has no idea of characters, word-level timing, SFX, or cost control on the Pro plan.

## (c) Can we write a better skill for our styles? Yes.

"Better" here means narrower and executable: it knows our files, commands, styles and finance data, and it checks things with small scripts instead of long prose (cheaper in tokens and more reliable). We should write it **in our own words**: copying their text would bring GPL licence terms into our project. Ideas aren't covered by the licence, only the wording.

Proposed contents (to be finalised in the architecture plan, step 2):

```
.claude/skills/
  video-core/                 shared by every style
    SKILL.md                  the pipeline steps + exact commands (short)
    references/
      plan-schema.md          every plan.json field, with examples
      explain-rules.md        explanation test + finance claim → visual table:
                                price over time → line chart + $ counter
                                drop → peak-to-trough marker with %
                                comparison → bars on one axis
                                compounding → growing stack / counter
      data-honesty.md         adjusted prices, source + date on screen,
                                every script number must exist in the data file
      review-checklist.md     contact-sheet review + per-beat sync checks
      known-errors.md         Node 22, Whisper misspellings, Meta AI quirks
    scripts/
      check_plan.py           plan.json valid? word indexes in range?
                                shot lengths inside the style's limits?
                                caption length OK? every number in script
                                found in the data file?
  style-vintage-story/        Style A
    SKILL.md                  measured look numbers, allowed shot types,
                              script pattern, Meta AI prompt template
    examples/plan.json        a known-good plan
  style-flat-fastcut/         Style B
    SKILL.md                  cut ~0.8 s, SFX per cut, rig poses, props
    examples/plan.json
```

Main ideas:
- **One shared core + one small skill per style.** New niche = new style folder, core unchanged.
- **Gates, but decided once per style**, not per video (voice, look, pacing are fixed in the style skill).
- **`check_plan.py` replaces most "do not" rules** with automatic checks Claude runs before rendering.
- Keep `SKILL.md` files short; long material sits in `references/` and is read only when needed (same trick they use; saves Pro-plan tokens).

## Recommendation
Don't install the OpenChatCut skill. Take its best ideas (explanation test, claim → visual table, honest-chart rules, sync checklist, hardest-section-first) and write them ourselves into the skill layout above as part of the architecture plan (next step).
