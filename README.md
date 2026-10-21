# Tangerang Housing Marketing Agent

A small AI agent that makes, publishes and tracks short-form marketing content for **Anggrek Permai**, our residential housing project in Tangerang (outside Jakarta, Indonesia).

## Goal

**Get potential buyers to contact us directly on WhatsApp (0851-9980-6283).** Every video and post exists to drive that.

**End state** (confirmed by the team on 2026-10-21):
1. **Make** the designs: videos and posts, built from our real footage in the campaign style (`editing/`, `docs/brand-style.md`, `docs/platform-strategy.md`).
2. **Post** them: 1–2 a day on TikTok and Instagram.
3. **Check engagement** on every post: saves, comments, shares, likes and views.
4. **Count WhatsApp contacts** and link them back to the post that brought them in, since that is the number that matters.
5. A weekly report on which videos bring saves, comments and WhatsApp contacts, and what to make next.

## Scope

The agent now covers the whole loop: **make → post → track → report**. Video creation was originally out of scope; it moved in once the render pipeline (`editing/render.py`) was working.

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
0. Make (editing/render.py) ──► Google Drive "To Post" ──► 1. Post ──► Drive "Posted"
                                                              │
                                                              ▼
                 3. Weekly report ◄── 2. Track engagement + WhatsApp contacts (Google Sheet)
```

0. **Make.** Shot lists in `editing/specs/` are rendered from the raw footage with `editing/render.py`, using only approved facts. Drafts go to the team for review before posting.
1. **Post (1–2× a day, Instagram).** Take the next video from Drive `To Post`. Use the caption from a matching text file if there is one; otherwise Claude writes one (Bahasa Indonesia first, plus hashtags and a contact CTA). Publish as a Reel, log it in the Sheet, and move the video to `Posted`.
2. **Track (daily).** Pull views, reach, likes, comments, shares, saves and follows for each post into a Google Sheet. **WhatsApp contacts** are logged in the same Sheet: each post's caption links to WhatsApp with a short pre-filled message that names the post (for example "Halo, saya lihat video Rumah Siap Huni"), so the team can see which post a chat came from. How the team records chats (by hand, or WhatsApp Business labels) is still to be decided.
3. **Weekly report.** Claude reads the Sheet and emails a short summary: which videos brought the most saves, comments and WhatsApp contacts, patterns (theme, length, hook, time) and suggestions for next week's videos.

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
- [ ] **Phase 0.5 — Make content** (in progress)
  - [x] Footage catalog (`footage-index/catalog.csv`)
  - [x] Approved facts, brand style, platform strategy, hook bank
  - [x] Render pipeline in the posted-TikTok style (`editing/render.py`)
  - [ ] First TikToks approved by the team, with music
  - [ ] Instagram (calmer, longer) template
- [ ] **Phase 1 — Posting:** Instagram posted by the agent from Drive on a schedule, with a caption review step at first; TikTok by hand
- [ ] **Phase 2 — Tracking:** daily engagement (saves, comments, shares, likes, views) plus WhatsApp contacts per post into the Google Sheet
- [ ] **Phase 3 — Weekly report:** Claude-written summary by email, ranked by saves, comments and WhatsApp contacts
- [ ] **Later (optional):** TikTok stats via API or a scheduler; replying to comments

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
/editing      Render pipeline, shot lists (specs/) and assets (logo, fonts)
/footage-index  Catalog of the raw footage
/agent        Reserved for later
```
