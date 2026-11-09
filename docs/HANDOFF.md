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
- **Both tests rendered with the new engine** (owner allowed rendering outside the sandbox): `runs/2026-11-09_test-vintage-nvda/out/final.mp4` (43 s) and `runs/2026-11-09_test-flat-timing/out/final.mp4` (18 s), −14 LUFS, reviewed; two vintage images re-cropped to hide numbers Meta AI invented. Renders must run outside the sandbox.
- **Cleanup done (owner's request):** legacy `YouTubeAutomation/` (code + 30 old videos + assets) and `experiments/` moved to the macOS Trash; legacy code also in git history (`git show 3c768e1:YouTubeAutomation/<path>`). Project folder now ~2.8 GB (mostly `engine/` venv + node_modules).

## 3. Next steps (in order)
1. Owner: watch both test videos and give feedback.
2. Owner: Tiingo free key (`TIINGO_API_KEY` in `.env`) → re-fetch NVDA daily, re-check facts; `SEC_USER_AGENT` ("Name email") for SEC data.
3. Owner: create GitHub repo (private recommended); Claude lists files before first push.
4. First production-length video (2:00–2:48) following `video-core` + measure Pro usage with `/usage`.
5. Open items: licensed music + real SFX, more Kokoro voice auditions, Skulsy pose set for vintage style.
