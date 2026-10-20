# Tangerang Housing Marketing Agent

A small AI agent that publishes short-form marketing videos for **Anggrek Permai**, our residential housing project in Tangerang (outside Jakarta, Indonesia). It tracks how they perform and sends a weekly report on what works.

## Goal

Build interest among potential home buyers through steady, engaging short-form video.

**End state:**
- 1–2 short videos are published every day on Instagram Reels and TikTok.
- Engagement is tracked for every post.
- A weekly report shows which videos perform best and what to make next.

## Scope

**Videos are made outside the agent**, with our own tools, and dropped into a Google Drive folder. The agent does **not** create video content. It only posts, tracks and reports.

| Platform | Posting | Stats |
|---|---|---|
| Instagram | Automated by the agent | Pulled automatically by the agent |
| TikTok | **Manual for now**, posted by hand in the TikTok app | To be decided (manual entry or TikTok API for Business) |

TikTok's developer rules don't allow apps that only post to your own account (see `docs/phase0-setup.md`), so TikTok stays manual unless we adopt an approved scheduler later.

## Accounts

| Platform | Handle | Type |
|---|---|---|
| Instagram | `anggrekpermai.official` | Business |
| TikTok | `anggrekpermai.offical` (check spelling) | Business |

## How it works

```
Our editing tools ──► Google Drive "To Post" ──► 1. Post ──► Drive "Posted"
                                                    │
                                                    ▼
                         3. Weekly report ◄── 2. Track (Google Sheet)
```

1. **Post (1–2× a day, Instagram).** Take the next video from Drive `To Post`. Use the caption from a matching text file if there is one; otherwise Claude writes one (Bahasa Indonesia first, plus hashtags and a contact CTA). Publish as a Reel, log it in the Sheet, and move the video to `Posted`.
2. **Track (daily).** Pull views, reach, likes, comments, shares, saves and follows for each post into a Google Sheet.
3. **Weekly report.** Claude reads the Sheet and emails a short summary: top and bottom videos, patterns (theme, length, time, hook) and suggestions for next week's videos.

## Google Drive layout

```
Anggrek Permai Marketing/
  To Post/     finished vertical videos (optional .txt caption with the same name)
  Posted/      moved here by the agent after publishing
```

## Tech stack

| Need | Choice |
|---|---|
| Runs on | Google Cloud: Cloud Run Job + Cloud Scheduler (no always-on server) |
| Agent brain | Claude via the Anthropic API (captions, weekly report) |
| Instagram | Instagram API with Instagram Login (Business account; no Facebook Page needed) |
| Video handoff | Google Drive |
| Post log and metrics | Google Sheets |
| Weekly report | Email |
| Secrets | Google Secret Manager (never in this repo or in chat) |

## Roadmap

- [ ] **Phase 0 — Setup**
  - [x] Business accounts on Instagram and TikTok
  - [x] ~~Instagram linked to a Facebook Page~~ (not needed with Instagram Login)
  - [ ] Meta developer app (on hold; steps in `docs/phase0-setup.md`)
  - [ ] Drive folders `To Post` / `Posted` created
  - [ ] Baseline metrics recorded (followers, average views per post)
  - [ ] Confirm TikTok handle spelling
- [ ] **Phase 1 — Instagram posting:** agent posts from Drive on a schedule, with a caption review step at first
- [ ] **Phase 2 — Tracking:** daily metrics into the Google Sheet
- [ ] **Phase 3 — Weekly report:** Claude-written summary by email
- [ ] **Later (optional):** TikTok stats, a scheduler for TikTok posting, in-house video creation (see `docs/style-references.md`)

## Risks and guardrails

- **Accuracy:** prices, promos and legal claims in captions must be correct. Keep an approved-facts file the agent must use, and never invent numbers.
- **Platform rules:** respect API posting limits and terms.
- **Brand safety:** review captions before posting until quality is consistent.
- **Account security:** store API tokens as secrets, never in this repo.

## Repo structure

```
/publishing   Instagram posting code
/analytics    Metrics collection and weekly report
/config       Approved facts, caption guidelines, schedule
/docs         Notes and decisions
/agent, /editing, /footage-index   Reserved for later (content creation is out of scope for now)
```
