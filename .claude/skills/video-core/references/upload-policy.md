# Upload: platform rules + SEO (all niches)

Checked 2026-11-10. Rules change often: re-check the official pages every ~3 months and update this file.
Sources: Meta, "Rewarding Original Creators on Facebook" (about.fb.com, March 2026); YouTube "inauthentic content" update (TechCrunch, 2026-07-20). Third-party guides were used only for detail and are marked "unverified" where they disagree.

## 1. What gets channels demonetized (and what we do about it)

| Platform rule | What it means for us | Our protection |
|---|---|---|
| **YouTube: inauthentic content** (generic, repetitive, template-based; mass-produced). Enforced on the **whole channel** | 3–4 videos/day in one format is exactly what this rule watches | Every video is a new story with its own characters and images; vary the formula (topic bank: never the same formula 3 in a row); real voice-over script written per video; no re-uploads of the same video with small changes |
| **YouTube: AI personas on sensitive topics (health, finance)** | Money is a sensitive topic | No "expert" persona and no advice: stories are clearly fiction/lessons; real numbers sourced (`facts.json`); "not financial advice" line; no promises ("guaranteed", "get rich") — banned in `niche.json` |
| **YouTube: off-putting / emotionally manipulative** | Fake shock hooks, distress bait | Hooks are honest situations, never invented science or fake "studies show" |
| **Meta: unoriginal content** (reposts, light edits, narrating others' content, stitched clips). Penalty: account non-recommendable + demonetized | Copying the reference page's stories or images | Stories written from our seeds, images generated per video, no clips from other creators, no reference footage ever uploaded |
| **AI disclosure** (both platforms: realistic synthetic people, voices, events) | Cartoons aren't realistic, but the voice is AI | Be safe: on YouTube set "Altered or synthetic content" = **Yes**; on Facebook add the **AI info** label. The label does not reduce monetization; hiding AI use can be penalized |
| **Copyright** | Music, images, fonts | Music only from `library/music.json` with a licence entry; images are ours (Meta AI output); system fonts |
| **Made for kids (YouTube)** | Stickman cartoons can look like kids' content | Set **"No, not made for kids"** (adult money/relationship topics). Wrong "kids" = no personalised ads, comments off |
| **Spam & misleading metadata** | Clickbait titles, tag stuffing, unrelated tags | Title matches the story; 8–15 relevant tags; 3–5 hashtags |
| **Meta: engagement bait** (long-standing rule: posts that explicitly ask to share, tag, like or comment get less reach) | Our stickman scripts end with "send this to…" | Prefer a soft, story-shaped ending ("Somewhere, someone just got their first paycheck.") and put the question in the caption, not "share this". Never "tag 3 friends" / "comment YES" |
| **Same video on both platforms** | Fine: it's our own original video | Upload natively to each (no TikTok/other watermarks); don't post the same video on several of our own pages |

Unverified (third-party only, don't rely on): a YouTube three-strike AI suspension system; Facebook monetization being invite-only.

## 2. Before every upload (owner checklist)
- [ ] Watched the whole video once with sound.
- [ ] `review/facts_review.md` ticked (every real number has a source).
- [ ] Story is ours (not a retelling close to another creator's video).
- [ ] Music licence recorded in `library/music.json`.
- [ ] YouTube: AI disclosure = Yes; Made for kids = No; category set; title ≤ 70 characters.
- [ ] Facebook: AI info label on; caption pasted; no hashtag spam.
- [ ] US audience (§4): language English (US) set; posted at the `Post at` slot.

## 3. SEO: how `upload.md` is written

**Title** (YouTube ≤ 70 chars visible; Facebook: first line of the caption)
- The hook in plain words + a curiosity gap; the main keyword early ("saving money", "first paycheck").
- No ALL CAPS, max 1 emoji, no promises. Write 3 options; the owner picks.

**Description / caption**
- Line 1–2: the hook again + what the viewer will learn (search engines read this first).
- The moral, as a quote.
- A question for comments ("Which brother are you?") — comments and shares drive reach.
- Disclaimer: "A fictional story for learning, not financial advice." + "Illustrations and narration made with AI tools; story written by us."
- 3–5 hashtags at the end (1–2 broad, 2–3 specific).

**Tags (YouTube only)**: 8–15, most specific first: topic phrase, lesson phrase, format ("moral story", "stickman animation"), audience ("money tips for beginners").

**Posting**: 3–4 a day is fine if every video is original; spread them over the US slots in §4. Reply to early comments; pin a comment with the question.

## 4. Reaching a US audience (all niches, every `upload.md`)

Owner's goal: US viewers (higher ad rates). Added 2026-11-10 (session 4).

**Posting times (US Eastern).** Spread a day's videos over these slots and put the slot in each `upload.md` (Eastern + India time; the owner posts from India):

| Slot | Eastern (EST, Nov–Mar) | India (IST) | Eastern (EDT, Mar–Nov) → India |
|---|---|---|---|
| Morning | 8:00 AM | 6:30 PM | 8:00 AM → 5:30 PM |
| Lunch | 12:30 PM | 11:00 PM | 12:30 PM → 10:00 PM |
| Evening (best) | 7:00 PM | 5:30 AM next day | 7:00 PM → 4:30 AM next day |
| Late evening | 9:00 PM | 7:30 AM next day | 9:00 PM → 6:30 AM next day |

US clocks change on the 2nd Sunday of March and the 1st Sunday of November; India doesn't, so the India time moves by one hour. Use Meta Business Suite / YouTube Studio scheduling for the night slots.

**Write for Americans** (script, title, caption): US dollars, US spelling and words (paycheck, mom, neighbor, savings account, 401(k), credit card, rent, grocery store), US settings (suburbs, diners, pickup trucks, school buses). No rupees, no UK spelling.
Note: the earlier stickman runs use "neighbours"; new scripts use US spelling.

**Settings in every `upload.md`:**
- YouTube: Video language **English (United States)**; title/description language **English (United States)**.
- Facebook: Page language English (US) (set once); post as a Reel from the niche's Page.
- `Post at:` one slot from the table above (a day's videos never share a slot).

**Hashtags:** 3–5 per post = the niche's base set (niche skill, "Upload text") + 1–2 story-specific. One US-flavoured tag only when it fits the story (#AmericanDream, #MiddleClass, #FirstJob). Never a stuffed list.

**Engagement without bait:** the comment question goes in the caption (and the pinned comment), never in the narration. Never "share if you agree", "tag a friend", "type YES".

**Paid boost (optional, owner's money):** Facebook "Boost" a post that is already doing well, audience = United States, age 25–60. Never needed for monetization.

**Facebook Page setup (once per niche):** up to 3 categories. Never "Financial Service" / "Financial Planner": they claim we give financial advice. Page name, bio and categories live in the niche skill.
