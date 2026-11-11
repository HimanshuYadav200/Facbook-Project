# Log: parmesan-bank

| when | step | notes |
|---|---|---|
| 2026-11-11 | created | niche strange-money, style explainer-fast |
| 2026-11-11 | research | Read in full: Wikipedia "Credito Emiliano" + "Parmesan" (raw wikitext), HBS Working Knowledge 2015, USDA FAS GAIN IT9029 (2009 PDF), CNN May 2026. NYT 2009 (seed source) not readable (paywall; archive fetch blocked). Disagreements: start year 1953 (Wiki, HBS) vs 1954 (USDA) → script says "since the 1950s"; wheels 440,000 capacity (HBS/Wiki/USDA 2009) vs 500,000 kept (CNN 2026) → 500,000 used, marked manual; LTV 70-80% (HBS) vs 60-80% (CNN) → "up to 80%"; weight 36 kg (Wiki Credem) vs 38 kg (Wiki Parmesan) → "about 80 pounds". 13 facts in facts.json |
| 2026-11-11 | script | 213 words, US spelling; hook "In Italy, a bank keeps 500,000 wheels of cheese in its vaults." |
| 2026-11-11 | voice | am_puck 1.15, no gap → 53.8 s, 95% heard as written (names Parmigiano Reggiano / Credito Emiliano) |
| 2026-11-11 | plan | 29 shots (median ~1.8 s), 25 motion graphics, actors: cheesemaker x2, banker x3 |
| 2026-11-11 | images | meta.ai own chat (tab of its own), full style block in every prompt, 2 per batch, saved by name as sm4_<name>.<ext> with blob-type extension (all webp, 1152x2048), wait-until-stable 4 s before each save. 25 images done in parallel mode; then coordinator ordered serial mode (owner's Mac overheating) → tab closed, waited for runs/strange-money/.browser.lock for the last 3 (banker actors). Files moved by name into img/ and img/green/ (no match_images: names are explicit, so no time-order risk; also match_images expects "name: prompt" lines while this format uses "name | prompt"). md5 duplicate check: none |
| 2026-11-11 | images (serial) | Took runs/strange-money/.browser.lock 08:56, reopened own chat in a new tab, made the 3 banker actors, closed tab, released lock. On reload Meta lazy-loaded an older image as "fresh" → helper now takes the newest and skips older ones; checked: right picture saved. 28 images total (21 scenes, 2 backgrounds, 5 actors), all webp 1152x2048, no duplicates. key_green: 5 clean cut-outs (review/green_check.jpg). Contact preview: no invented text/numbers seen |
| 2026-11-11 | check | check_plan: 0 errors, 2 warnings (manual facts vault_wheels, never_lost) |
| 2026-11-11 | render v1 | render lock taken/released; final.mp4 54.7 s, −14.3 LUFS, true peak −1.2 dB. Review round 1 → review/round_1.md (stamp over face, tiny labels, circle position). v1 kept as out/v1_raw.mp4, out/v1_final.mp4 + plan_v1.json |
| 2026-11-11 | render v2 | fixes applied; check_plan 0 errors; final.mp4 54.7 s, −14.3 LUFS, true peak −1.2 dB. Round 2 OK (YES! stamp briefly overlaps the name label mid-slam: left). facts_review.md written; upload.md (Post at: Late evening 9:00 PM Eastern) |
