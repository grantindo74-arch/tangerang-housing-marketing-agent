# Tangerang Housing Marketing Agent

An autonomous AI agent that turns raw footage of our residential housing project in Tangerang (outside Jakarta, Indonesia) into short-form marketing videos. It publishes them daily to Instagram and TikTok, tracks how they perform, and improves the content over time.

## Goal

Build interest among potential home buyers through steady, engaging short-form video.

**End state:**
- 1–2 short videos are published every day on Instagram Reels and TikTok.
- Themes vary, and each video has music and effects.
- The agent runs on its own, from picking footage through to publishing.
- A weekly report shows which videos perform best, and the content mix shifts toward what works.

## Accounts

| Platform | Handle | Type |
|---|---|---|
| Instagram | `anggrekpermai.official` | Business |
| TikTok | `anggrekpermai.offical` (check spelling) | Business |

## How it works

```
Raw footage library ──► 1. Select clips ──► 2. Edit video ──► 3. Write caption ──► 4. Publish
                                                                                        │
          ┌─────────────────────────────────────────────────────────────────────────────┘
          ▼
   5. Collect metrics ──► 6. Weekly report ──► 7. Adjust content plan ──► (back to 1)
```

1. **Select clips.** Pick footage from the raw video library that fits today's theme. Tag clips by scene (exterior, interior, amenities, construction progress, neighborhood, drone) so they're easy to find.
2. **Edit video.** Cut a vertical 9:16 video, 15–45 seconds long, with music, transitions, text overlays and a call to action.
3. **Write caption.** Bahasa Indonesia first, with optional English, plus hashtags and a contact or link CTA.
4. **Publish.** Post to Instagram and TikTok through their official APIs at the best posting times.
5. **Collect metrics.** Pull views, watch time, likes, comments, shares, saves, follows and link clicks for each post.
6. **Weekly report.** Rank videos, compare themes, and call out what's working and what isn't.
7. **Adjust content plan.** Shift next week's theme mix toward the best performers, and keep some room for experiments.

## Content themes (starting rotation)

| Theme | Example |
|---|---|
| Home tour | Walk-through of a show unit, room by room |
| Construction progress | Before/after or time-lapse of building phases |
| Lifestyle | "A day living here": morning coffee, kids playing, commute |
| Amenities | Pool, park, clubhouse, security, playground |
| Location | Distance to toll roads, malls, schools, airport (CGK), Jakarta |
| Price and promos | Payment plans, KPR info, limited-time offers |
| Trends | Trending audio or meme formats adapted to the project |
| FAQ | Quick answers to common buyer questions |

## Tech stack (proposed)

| Need | Options |
|---|---|
| Agent brain / orchestration | Claude (Agent SDK or API) on a daily schedule |
| Video editing | FFmpeg / MoviePy for scripted editing; a template tool like Creatomate or Shotstack for richer effects |
| Music | Licensed or royalty-free library (avoid copyright strikes) |
| Footage storage | Google Drive or cloud storage (S3/GCS) |
| Instagram | Instagram API with Instagram Login (Business account; no Facebook Page needed, see `docs/phase0-setup.md`) |
| TikTok | TikTok Content Posting API + Display API (needs app review, then an audit before posts can be public) |
| Data | Simple database (SQLite/Postgres) or Google Sheets for post and metrics history |
| Reports | Weekly email, Google Doc, or dashboard |

## Roadmap

- [ ] **Phase 0 — Setup:**
  - [x] Business accounts on Instagram and TikTok
  - [x] ~~Instagram account linked to a Facebook Page~~ (not needed with Instagram Login)
  - [ ] Meta and TikTok developer apps (walkthrough: `docs/phase0-setup.md`)
  - [ ] Footage library organized and tagged
  - [ ] Baseline metrics recorded (followers, average views per post)
- [ ] **Phase 1 — Editing:** the agent produces good videos from raw footage, with a human reviewing every video before it's posted
- [ ] **Phase 2 — Publishing:** automated posting to Instagram and TikTok on a schedule
- [ ] **Phase 3 — Analytics:** metrics collection and weekly report
- [ ] **Phase 4 — Feedback loop:** the agent adjusts themes and style based on results
- [ ] **Phase 5 — Full autonomy:** reduce human review to spot checks once quality is proven

## Risks and guardrails

- **Accuracy:** prices, promos and legal claims must be correct. Keep an approved-facts file the agent must use, and never invent numbers.
- **Music copyright:** only use licensed tracks, especially for business accounts.
- **Platform rules:** respect API posting limits and terms; TikTok API approval can take time.
- **Brand safety:** a human approval step until quality is consistent.
- **Account security:** store API tokens as secrets, never in this repo.

## Repo structure (planned)

```
/footage-index    Catalog and tags for raw clips (not the videos themselves)
/agent            Agent logic: planning, selection, captioning
/editing          Video templates and editing scripts
/publishing       Instagram and TikTok posting code
/analytics        Metrics collection and weekly reports
/config           Themes, brand guidelines, approved facts
/docs             Notes and decisions
```
