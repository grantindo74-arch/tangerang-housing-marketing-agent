# Phase 0 — Platform setup walkthrough

Step-by-step setup for the Instagram and TikTok APIs, written for doing on a phone.

> **Phone tip:** the Meta and TikTok developer sites are built for desktop. In Chrome or Safari, open the browser menu and turn on **"Desktop site"** before starting.
>
> **Security:** when a site shows you an access token, App Secret or Client Secret, do **not** paste it into chat or into this repo. Save it in the Claude Code environment's secrets settings (names below).

---

## Decision: Instagram does not need a Facebook Page

Meta now offers two ways to use the Instagram API:

| | Instagram API with **Instagram Login** | Instagram API with **Facebook Login** |
|---|---|---|
| Facebook Page needed | **No** | Yes |
| Publish Reels | Yes | Yes |
| Read insights (views, likes, etc.) | Yes | Yes |
| Ads, hashtag search, tagging | No | Yes |

We only need publishing and insights, so we use **Instagram Login** and skip the Page link. If we later want to run paid ads from the same setup, we can link a Page then.

---

## 1. Meta (Instagram) developer app

**You need:** a personal Facebook account (Meta developer accounts are tied to one), and the login for `anggrekpermai.official`.

1. **Become a Meta developer.**
   1. Go to **developers.facebook.com** and log in with Facebook.
   2. Tap **Get Started**. Accept the terms and verify your phone number or email.
   3. For "Which describes you best", choose **Developer**.
2. **Create the app.**
   1. Go to **My Apps → Create App**.
   2. App name: `Anggrek Permai Marketing Agent`. Contact email: your work email.
   3. Use case: **"Manage messaging & content on Instagram"**.
   4. If asked for a business portfolio, select the Anggrek Permai one if it exists. Otherwise choose "I don't want to connect a business portfolio yet".
   5. Finish and open the app dashboard.
3. **Set up Instagram Login.**
   1. In the left menu, go to **Use cases → Customize** (or **Instagram → API setup with Instagram login**).
   2. Under **Generate access tokens**, tap **Add account** and log in as `anggrekpermai.official`. Approve the permissions.
   3. Check that these permissions are listed: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights` (and optionally `instagram_business_manage_comments`).
   4. **Don't generate or copy a token yet.** We'll do that together in Phase 2, straight into secrets.
4. **Note these values** (go to App settings → Basic). They go into secrets in Phase 2, not into chat:
   - `META_APP_ID`. This is not secret, so you can share it.
   - `META_APP_SECRET`. This **is** secret.
5. **App Review: probably not needed.** The app only posts to our own account, and that account has a role on the app. That works in Development mode. Meta may ask for Business Verification or App Review later. If it does, send me a screenshot and I'll walk you through it.

**Done when:** the app exists and `anggrekpermai.official` appears under "Generate access tokens".

---

## 2. TikTok developer app

> **⚠️ On hold (2026-10-19).** TikTok's Content Sharing Guidelines list "a utility tool to help upload contents to the account(s) you or your team manages" as **not acceptable** for the Content Posting API. That describes our agent, so the audit for public posting would likely fail. Current plan:
> - **Posting to TikTok:** use an approved scheduler (Metricool, Buffer, Later, …), or post by hand.
> - **TikTok stats:** check whether the **TikTok API for Business (Organic API → Accounts)** covers a brand's own account. If not, use the scheduler's analytics export.
>
> The steps below are kept for reference only.

**You need:** the login for the TikTok Business account, plus a **website** with a Privacy Policy page and a Terms of Service page. TikTok requires both URLs, and you have to prove you own them (see 2.4).

1. **Confirm the handle.** In the TikTok app, go to **Profile**. The handle is the `@name` under the profile photo. Is it `anggrekpermai.offical` (no "i") or `anggrekpermai.official`? If it's misspelled, you can change it under **Edit profile → Username**, once every 30 days. Do that now, before the API app is approved.
2. **Register as a developer.**
   1. Go to **developers.tiktok.com** and tap **Log in**. Use the email you want to own the app; it can differ from the TikTok account.
   2. When asked, create an **Organization** named "Anggrek Permai" rather than "Individual".
3. **Create the app.**
   1. Go to **Manage apps → Connect an app** (or **Create app**).
   2. Fill in: app icon (the logo, 1024×1024), name `Anggrek Permai Marketing Agent`, category **Business / Marketing**, and a short description: *"Internal tool that publishes Anggrek Permai's own marketing videos to our TikTok account and reads their performance."*
   3. Platform: **Web**. Enter the website URL, the Terms of Service URL and the Privacy Policy URL.
4. **Add products and scopes.**
   - **Login Kit**
   - **Content Posting API**, with **Direct Post** turned on
   - Scopes: `user.info.basic`, `user.info.stats`, `video.upload`, `video.publish`, `video.list`
5. **Verify URLs.** TikTok gives you a small verification file or a DNS TXT record for each URL. Send me a screenshot and I'll tell you exactly where it goes.
6. **Submit for review.**
   - Explain each product and scope ("`video.publish`: publish our own edited marketing videos to our account", "`video.list`/`user.info.stats`: weekly performance report", etc.).
   - Upload a **demo video** of the end-to-end flow. We don't have one yet. Options: submit Login Kit first and add posting later, or wait until Phase 2 produces a working demo. Either way, **create the app and verify URLs now**, because that part takes the longest.
7. **Audit (later).** Until TikTok audits the app, API posts can only be **private** ("only me") and the account must be set to private while posting. Public posting needs a separate audit after review. Plan for this in Phase 2. Until then, Phase 1 videos can be posted by hand.

**Done when:** the app is created, URLs are verified, and the review is submitted (or ready to submit with a demo).

---

## Open questions

- [ ] Correct TikTok handle (spelling)
- [ ] Do we have a website domain for Privacy Policy and Terms pages? If not, Claude can draft both and host them free on GitHub Pages.
- [ ] Does Anggrek Permai have a Meta business portfolio (Business Manager)?

## Secrets to create later (Phase 2)

| Name | From |
|---|---|
| `META_APP_ID`, `META_APP_SECRET` | Meta app → App settings → Basic |
| `INSTAGRAM_ACCESS_TOKEN` | Generated in Phase 2 |
| `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | TikTok app → App details |
| `TIKTOK_ACCESS_TOKEN` / refresh token | Generated in Phase 2 |
