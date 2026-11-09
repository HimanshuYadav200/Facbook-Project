# Ponytail skill: analysis (2026-11-09)

Owner asked to analyse `github.com/DietrichGebert/ponytail` (suggested install: `git clone`). Files were read from GitHub as plain text. **Not cloned or installed.**

- ≈187k stars, MIT licence, created Jun 2026, v5.3.3.
- **It is not a video-editing skill.** It is a *coding-style* skill: "Makes your AI agent think like the laziest senior dev in the room. The best code is the code you never wrote." No mention of video, Remotion or ffmpeg anywhere.

## How it's built

| Part | What it is |
|---|---|
| `skills/ponytail/SKILL.md` (3.5 KB) | The core: write the smallest change that fully solves the task |
| 5 more skills | `ponytail-review`, `-audit`, `-debt`, `-gain`, `-help` (code review / bloat audit / tech-debt list / stats) |
| Claude Code plugin + hooks | Node scripts that run on **every session start, every prompt and every subagent** to keep the mode switched on |
| "Band" task board | On by default: after every turn writes a row (cost, turns, tokens, tests) to `~/.config/ponytail/band/<project>.csv`. Optional webhook (off by default) can send it to a URL |
| Copies for ~20 other agents | Cursor, Copilot, Windsurf, Codex, etc. (same rules) |
| Benchmarks, tests, examples | Their claim: −53% code, −45% tokens, more tests, in Claude Code on Opus 5.5 |

### The core rules (SKILL.md)
Pick the first option that fully works:
1. Does it need to exist? Skip features nobody asked for.
2. Already in the codebase? Reuse it.
3. Standard library / platform feature?
4. An installed dependency? (never add one for a few lines)
5. One readable line?
6. Otherwise the minimum code.

Plus: finish everything the change touches (callers, tests); no "for later" abstractions; small test for non-trivial logic (money, parsers); mark shortcuts with `shortcut: <limit>, <when to upgrade>`; never cut validation, security, data-loss protection; end each reply with what was skipped and any risk.

## Is it useful for us?

**Not for the videos.** It says nothing about scripts, visuals, timing, captions or style. It does not replace the video skills proposed in `docs/OPENCHATCUT_SKILL_ANALYSIS.md`.

**Somewhat useful for building the engine code.** Its rules match the owner's rule "prefer simple, documented components the owner can understand and fix": less code = less to understand. The "small test for money logic" and "shortcut:" comments fit too.

**Cautions:**
- The full plugin adds background hooks to every Claude Code session (all projects, not just this one) and logs task stats to `~/.config` by default. More moving parts than we need.
- Its "push back / skip features" style (especially `ultra`) could clash with "plan → agree → build": the owner decides scope, not the skill.
- "Smallest diff" must not win over clear documentation; our docs rules stay on top.

## Recommendation
Don't install the plugin. If the owner likes the idea, use the light option: add its six-step "smallest complete change" ladder and the `shortcut:` comment rule (MIT, so copying is fine with credit) to this project's `CLAUDE.md`, or copy only `skills/ponytail/SKILL.md` into `.claude/skills/` with no hooks. Decide when we start building the engine (after the architecture plan).
