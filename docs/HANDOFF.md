# Session Handoff (end of session 2, 2026-11-09)

> New chat? Read this file first. It is the compact state of everything up to now.
> Detail: `docs/CONTEXT.md` (requirements, decisions, session log) · `docs/ARCHITECTURE.md` (how the engine works) · `docs/LEGACY_AUDIT.md` (everything found and fixed) · `docs/RESEARCH_REVIEW.md` (why research changed) · `engine/README.md` (setup + tools) · `.claude/skills/video-core/SKILL.md` (how to make a video).

## 1. What we're building
A local, Claude-directed engine that makes **faceless vertical videos (2:00–2:48)** for **Facebook first, then YouTube**, uploaded **manually**. First niche: **Skulsy (cartoon skeleton) + USA finance**. Must be **monetizable**: real data, story, motion graphics, not an AI slideshow. Free/open-source first. MacBook Pro (24 GB). Brain = **Claude Code on the owner's personal Pro plan** (never the office account). Target ~3 videos/day later; new niches = new skills.

Owner's rules: **plan → agree → build**; document everything; log decisions in `docs/CONTEXT.md`; coding rules in `CLAUDE.md`.

## 2. Where things stand
- **Architecture v1.2 approved and built** (B1–B5). Layout: `engine/` (tools + Remotion), `.claude/skills/` (video-core, style-vintage-story, style-flat-fastcut, niche-skulsy-finance), `library/` (sfx + index), `references/` (owner's material), `runs/` (one folder per video), `archive/` (old files, nothing deleted).
- **Local git repo**, 2+ commits, `.gitignore` excludes `.env`, media, caches, venvs. Not pushed: owner will create a GitHub repo.
- **Research replaced:** numbers only via `fetch_data.py` → `finance_calc.py` → `facts.json`; `check_plan.py` refuses any script/on-screen number not in facts.json. 32 tests pass.
- **Both style tests converted** to `runs/2026-11-09_test-vintage-nvda` and `runs/2026-11-09_test-flat-timing`, with corrected numbers (66% drop, $41,100, $262,000), new voices (British fix), both pass check_plan.
- **Not done: rendering with the new renderer.** It type-checks, but renders hang inside Claude Code's sandbox (headless Chrome can't reach Remotion's local server) and the auto-mode safety check refused running outside it. The old project hangs the same way inside the sandbox, so it's the environment, not the code.
- `YouTubeAutomation/` untouched. `experiments/` marked retired, kept until owner OKs deletion.

## 3. Next steps (in order)
1. **Owner: render the two tests** (outside the sandbox):
   `! engine/tools/render.sh runs/2026-11-09_test-vintage-nvda` and `! engine/tools/render.sh runs/2026-11-09_test-flat-timing`
   Then Claude: `finish.py --test`, `contact_sheet.py`, review, fix any renderer bugs.
2. Owner: Tiingo free key (`TIINGO_API_KEY` in `.env`) → re-fetch NVDA daily, re-check facts; `SEC_USER_AGENT` ("Name email") for SEC data.
3. Owner: create GitHub repo (private recommended); Claude lists files before first push.
4. Owner OK → delete `experiments/` (1 GB node_modules + 1.6 GB venv).
5. First production-length video (2:00–2:48) following `video-core` + measure Pro usage with `/usage`.
6. Open items: licensed music + real SFX, more Kokoro voice auditions, Skulsy pose set for vintage style.
