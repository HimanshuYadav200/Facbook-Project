# Log: eiffel-tower-sale

| when | step | notes |
|---|---|---|
| 2026-11-10 | created | niche strange-money, style explainer-fast |
| 2026-11-10 | research | Lustig story checked on Wikipedia + todayifoundout (cites Smithsonian); amounts and second-attempt delay disagree between sources → script names neither. Tower facts from Wikipedia |
| 2026-11-10 | voice | am_puck 1.15, no gap → 53.2 s, 214 words (~241 wpm), 98% heard as written |
| 2026-11-10 | images | 32 Meta AI images in one chat (19 scenes, 7 backgrounds, 6 green actors); key_green.py cut-outs clean. Police door shows "1920" + part of a sign |
| 2026-11-10 | render v1 | 33 shots, median 1.66 s; whip showed a black edge (station shot), laughing dealers cropped |
| 2026-11-10 | render v2 | whip shortened (+blur), laughing focus [0.5, 0.78]. final.mp4 54.1 s, −14.3 LUFS; speech −16.6 dB, pauses −34 dB. v1 kept as out/v1_*.mp4. Copy ~/Downloads/strange_money_eiffel_draft1.mp4 |
| 2026-11-10 | render mg (trial) | Motion graphics added (owner: try, else keep v2): 20 shots with stamps/labels/counters/arrows/money/speed lines/?!/X/circles + 1 green colour card ("highest bidder"). Red X moved onto the police door (also hides "1920"). final.mp4 54.1 s, −14.2 LUFS → ~/Downloads/strange_money_eiffel_mg.mp4. v2 kept as out/v2_*.mp4 + plan_v2.json |
| 2026-11-10 | render mg2 | Owner: mg1 great, but graphics' own wobble fought the shot wobble, and cuts came before graphics could be seen. Removed graphic jitter/line boil; new `hold` + 1 s minimum per graphic: 10 graphics fixed (earlier `at`, holds 0.15–0.35 s). final.mp4 54.1 s, −14.3 LUFS → ~/Downloads/strange_money_eiffel_mg2.mp4; mg1 kept as out/mg1_*.mp4. upload.md written (SEO) |
| 2026-11-10 | render sfx | Recorded SFX pools (sounds.json): variant per cut/graphic, stamp + punch layered. First try too loud (whooshes 3 dB, hits 0 dB under voice, measured on a voice-muted render) → defaults cut 0.22 / mg 0.35 / sfx 0.3 / crowd 0.25, boing −4 dB. final.mp4 54.1 s, −14.3 LUFS → ~/Downloads/strange_money_eiffel_sfx.mp4; mg2 kept as out/mg2_*.mp4 + plan_mg2.json |
| 2026-11-10 | render sfx2 | Owner: sound at "SOLD!" (repeated across the video) annoying/off-theme → removed impact_r2 ("quick zoom impact") from the impact pool. sfx1 kept as out/sfx1_final.mp4 → ~/Downloads/strange_money_eiffel_sfx2.mp4 |
