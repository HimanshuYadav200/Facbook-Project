# Session Handoff (end of session 3, 2026-11-10)

> **New chat? Read this file first.** It is the complete, compact state of the project.
> Then, as needed: `docs/CONTEXT.md` (requirements, every decision, session log) · `docs/ARCHITECTURE.md` (how the engine works, change log) · `.claude/skills/video-core/SKILL.md` (how to make a video, exact commands) · `engine/README.md` (setup + tools).
> Rules (from `CLAUDE.md`): **plan → owner agrees → build**; log every decision in `docs/CONTEXT.md`; follow the "Coding rules" in `CLAUDE.md`.

---

## 1. What we're building
A local, Claude-directed engine that makes **faceless vertical short videos** for **Facebook and YouTube**, uploaded **manually** by the owner. One skill per **niche** (content) and per **style** (look); Claude drives every step. Free / open-source first, runs on the owner's MacBook Pro (M5, 24 GB). Brain = Claude Code on the owner's personal Pro plan. Target: **3–4 reels/day per niche**, every video original (YouTube "inauthentic content" + Meta "unoriginal content" rules: `video-core/references/upload-policy.md`).

## 2. Niches: readiness for posting
| Niche | Style | Length | Status | First video | Before posting at volume |
|---|---|---|---|---|---|
| **strange-money**: true strange money stories, scams, loopholes; fast excited explainer | `explainer-fast` (AI 3D-cartoon images, camera moves incl. 3D tilts, green-keyed cut-out actors, **motion graphics**, recorded SFX pools, 1–3-word captions) | 45–70 s | **Ready.** Owner approved look + motion graphics + SFX | `runs/strange-money/2026-11-10_eiffel-tower-sale/out/final.mp4` (= `~/Downloads/strange_money_eiffel_sfx2.mp4`) + `upload.md` (SEO) | Owner ticks 2 manual facts in its `facts.json`; topic bank being grown to ~120 (see §5); pick voice (default `am_puck` 1.15) |
| **stickman-money**: calm stickman parables, one money lesson | `stickman-calm` (grey pencil-sketch images, slow camera, dissolves, karaoke captions, blinks, optional owner-supplied clips) | ~1:30 | **Ready** ("done for now") | `runs/stickman-money/2026-11-10_two-brothers-paycheck/out/final.mp4` (v4, 87.7 s) + `upload.md`. **Session 4: 3 more** (earn-ten-dollars, same-raise, parents-said-no), each with `upload.md` | Owner watches the 3 new videos + ticks their illustrative facts; 4 of 100 seeds used; fixes proposed for blinks/matching/image helper (CONTEXT session 4); Meta AI *video* isn't available in Claude's browser (owner supplies clips if wanted) |
| **skulsy-finance**: Skulsy cartoon skeleton + real USA finance data | `vintage-story` / `flat-fastcut` | 2:00–2:48 | **Not ready.** Only two short tests (43 s, 18 s) | `runs/skulsy-finance/2026-11-09_test-*` | Needs a production-length video, owner feedback, `TIINGO_API_KEY` + `SEC_USER_AGENT` in `.env` (real market data) |

## 3. Engine state
| Area | State |
|---|---|
| Tools | `engine/tools/`: new_run, fetch_data, finance_calc, voice (Kokoro + whisper), match_images, check_plan, render.sh, finish (−14 LUFS), contact_sheet, facts_review, make_sfx, find_eyes (blinks), key_green (green-screen cut-outs). **53 tests pass**: `engine/.venv/bin/python -m unittest discover -s engine/tests` |
| Renderer | `engine/remotion/` (Remotion 4.0.537, Node 22). Styles: vintage-story, flat-fastcut, stickman-calm, explainer-fast (`ExplainerFast.tsx`, `Graphics.tsx`, `sounds.json`) |
| explainer-fast extras | `mg` motion graphics per shot (stamp, label, counter, arrow, money, speedLines, marks, cross, circle, pointer; no own wobble; each ≥ 1 s on screen, checker-enforced), `bg` colour-card shots, `hold` (delay a cut 0–0.6 s), sound pools with per-cut variants; default volumes cut 0.22 / mg 0.35 / sfx 0.3 (measured: whooshes ~9 dB, hits ~6–8 dB under voice) |
| SFX library | `library/sfx/`: 21 generated + **47 recorded** (`*_r*`, Mixkit free licence + freesound CC0) → `library/sfx.json`, `library/sfx_incoming/review.md`, `preview.wav`. Owner removed `impact_r2`. **Mixkit licence: never share the files on their own, never use Content ID**; `*.wav` is git-ignored |
| Music | `library/music/the-end-soundaudio.mp3` (owner: non-copyright) |
| Images | Meta AI driven by Claude in Chrome (one chat per video; `saveNewest`, 2 images per batch). ~32 images per strange-money video ≈ 20 min: the throughput bottleneck at 3–4 videos/day |
| Blender | 5.3 installed (Homebrew). Test in the Eiffel run's `blender_test/`. **Parked for R&D** (output too crude); next try: Blender MCP with real models/textures |
| Git | Local repo, **not pushed**. Session 3 work committed on branch `session-3-niches` (221663d), not yet merged into `main`. Commit only when the owner asks |

## 4. Decided, not yet done
- **Local SFX model: Stable Audio 3 Small SFX** (owner, 2026-11-10: "we will go with the sfx local model", for future niches). Only commercially usable local option found (Stability Community License: free under $1M yearly revenue). Others (MMAudio, AudioGen, AudioLDM 2, Tango) are non-commercial. **Owner first:** (1) Hugging Face account → accept terms on `stabilityai/stable-audio-3-small-sfx`; (2) register with Stability AI for commercial use; (3) HF read token → `hf auth login`. **Then Claude:** install in a **separate venv** (`~/tools/stable-audio-3`, MLX path; it pins torch 2.7.1, so not in `engine/.venv`), test on the M5, add a `make_sfx`-style generator, licence entries in `sfx.json`. Research details: CONTEXT.md session log cont. 15.
- **Topic bank (strange-money): done.** `.claude/skills/niche-strange-money/references/topics.md` has **120 seeds** (S 25, L 24, B 24, O 24, D 23) with `Key facts` + `Sources`, series links (Lustig 1→21→31 Capone, Ponzi 8↔46, Prohibition 66→67→68…), a rejects list and a **first-week order** (21 videos, 3/day, type never twice in a row; starts with #31 Lustig cons Capone). Flagged: #10 (living private person: no name or skip), #11 tulips (tell "legend vs record"), #26 Gillette razor myth (tell "the story is backwards"), #27 cobra bounty + #28 salami fraud excluded, #30 Woolworth hook corrected. Weak sources to fix during research: #55, #57, #60, #62, #90. Every seed still needs its own research pass into `facts.json` (Wikipedia + 1 more source, read in full).

## 5. Waiting on the owner
1. strange-money: tick facts `lustig_1925` + `poisson_bribe` (manual), choose a title from `upload.md`, upload.
2. Local SFX model accounts (§4).
3. skulsy-finance: Tiingo key + SEC contact in `.env`; feedback on the two tests.
4. GitHub repo (private recommended): Claude lists files first; Mixkit WAVs must stay out.
5. Merge branch `session-3-niches` into `main` when happy (Claude can do it).

## 6. Next steps
0. (Session 4 cont. 6) Engine fixes done (ARCHITECTURE v1.8): `fact_check.py` (Tavily auto fact check; facts get `search` + `key`), `meta_save.js`, match_images by name, blinks under hair/glasses, `$365 million` allowed, true-peak check, 2-line labels, money `y`. 68 tests. Owner: pick a voice from `~/Downloads/voice_samples_strange_money/`; read the Eiffel (+0.1 dB peak) note. The 4 stickman videos still have their old eyes.json (re-run find_eyes + re-render only if the owner wants blinks added).
0. (Session 4) SFX overhaul done 2026-11-11: 147 sounds, local Stable Audio 3 (`engine/tools/gen_sfx.py`, model in `~/tools/stable-audio-3`), quieter/fewer explainer-fast sounds. Owner: register with Stability AI; download Sonniss GDC 2026 zips by hand. See CONTEXT session 4 (cont. 4).
0. (Session 4) Strange-money: 4 more videos done 2026-11-11 (Lustig-Capone, Ford van seats, Hanoi rats, Parmesan bank), each waiting on owner fact ticks; next in the first-week order: #105, #32, #4, #70. Engine issue list: CONTEXT session 4 (cont. 3). Run agents in serial browser mode (heat).
0. (Session 4) Stickman-money: parallel agents work (one per video, own Chrome tab, render lock in `runs/stickman-money/.render.lock`). Owner to decide on the 4 engine/skill fixes listed in CONTEXT.md session 4.
1. Produce strange-money videos from the first-week order in topics.md (video-core skill + niche/style skills).
2. Stability AI licence applied for (no confirmation yet): keep `gen_*` sounds out of uploads until it arrives.
3. Later scope (logged): multi-angle AI animation, Blender R&D, blinks on explainer actors, Lustig redesign (resembles a board-game mascot), more voices.

## 7. Traps (read before working)
- **Render outside the sandbox** (`render.sh` with sandbox disabled; owner allowed it). Otherwise headless Chrome can't reach Remotion.
- **zsh doesn't word-split `$VAR`**; `$n:l` is a zsh modifier. No `timeout` on macOS. ffmpeg here has **no drawtext**; PIL and librosa aren't installed (no new packages without owner OK).
- Never overwrite renders/plans: back up as `out/<tag>_final.mp4`, `plan_<tag>.json` first (the Eiffel run has v1, v2, mg1, mg2, sfx1 versions).
- Meta AI: invented text/numbers in images → check the contact sheet; a late image arrives as "2 new candidates".
- Kokoro: write "A I" not "AI"; numbers as digits in the script (checker); every on-screen number must be in `facts.json`.
- Blender headless: physics needs `bpy.ops.ptcache.bake_all(bake=True)`; `transform_apply` defaults also apply location.
- Owner preview without sound: use QuickTime/VLC.

## 8. Folder map
```
CLAUDE.md               project rules + coding rules
.env                    API keys (never commit/print)
docs/                   HANDOFF (this), CONTEXT, ARCHITECTURE, analyses
.claude/skills/         video-core, style-*, niche-* (skulsy-finance, stickman-money, strange-money)
engine/                 tools/, tests/, remotion/, .venv/ (Python 3.12)
library/                sfx/ + sfx.json + sfx_incoming/, music/ + music.json
references/             per-niche reference reels + analysis.md (skulsy-finance, stickman-psychology, Ricks-clips)
runs/<niche>/<date>_<slug>/   one folder per video: script, facts.json, voice, words, plan, img, review, out, upload.md, log.md
```
