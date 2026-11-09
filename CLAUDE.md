# Project instructions for Claude

Before doing anything in this project, read:
0. `docs/HANDOFF.md`: compact current state + next steps (start here).
1. `docs/CONTEXT.md`: requirements, decisions, open questions, session log.
2. `docs/ARCHITECTURE.md` (when it exists): detailed flow and change log.

Rules:
- Plan first. Do not change code until the owner has agreed on the plan for that change.
- After any decision or change, update `docs/CONTEXT.md` (decisions log + session log). For structural changes, also update `docs/ARCHITECTURE.md` (flow + change log with the reason).
- The owner must be able to understand and fix every part. Prefer simple, documented components over clever ones.

## Coding rules (apply every time you write or change code)

Adapted from the Ponytail skill (MIT, github.com/DietrichGebert/ponytail). The project rules above come first: the owner decides scope, and clear beats short.

**Before writing:** read the code the change touches and list every place it must reach (callers, plan.json readers, Remotion components, scripts, docs). That is the scope; extra features are not.

**Take the first option that fully works:**
1. Does it need to exist? Skip features, options and "for later" code nobody asked for; name what you skipped in one line.
2. Already in this project (a tool in `tools/`, a Remotion component, a helper)? Reuse it the way the surrounding code does.
3. Built into the language or our existing tools (Python stdlib, Remotion, ffmpeg)? Use that.
4. An already installed package? Use it. Never add a package for a few lines; any new dependency needs the owner's OK.
5. Otherwise, the minimum code that works and that the owner can read.

**While writing:**
- Finish everything the change breaks: callers, examples, docs, commands in READMEs.
- No wrappers, abstractions, config options or classes nobody asked for. Deleting code beats adding it. Keep the existing folder layout and conventions.
- Bug fix: find every caller first, then fix the root cause once in the shared code.
- Comment the *why* in one plain-English line, not the *what*.
- Non-trivial logic gets one small test or assert-based self-check: anything touching money/market numbers, word timings, plan.json parsing, or file overwrites.
- A known shortcut gets a comment: `# shortcut: <the limit>, <when to upgrade>`.

**Never cut:** checks on outside input (API data, plan.json written by Claude, downloaded images); protection against losing work (never overwrite renders, assets or images without a backup); secrets (`.env` keys never printed, logged or committed); anything the owner asked for.

**After writing:** end the reply with one or two lines saying what was skipped or not checked, and any risk the owner must know.
