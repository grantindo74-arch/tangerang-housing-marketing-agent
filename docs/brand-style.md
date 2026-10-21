# Brand style

**Source of truth for this campaign:** the Canva folder **AP Sosmed**, which holds one design, **"Thumbnail Tiktok"** (44 TikTok covers, Oct 2026). A local export of all 44 pages is in `Canva Tiktok/Thumbnail Tiktok/` on the shared drive.

Everything else in Canva (the billboard, the A5 brochures, the purple flyer, the website mock-up, the X-banner) is **older material. Don't take styles or facts from it.**

**Facts always come from `config/approved-facts.json`, never from Canva designs.**

Values below were read from the design's element data on 2026-10-21 (pages 1 and 23), not estimated from screenshots.

## Canvas

- Covers are **1080 × 1350** (4:5). Videos are 1080 × 1920; keep the logo and hook inside the central 4:5 area so the cover crop and the video frame match.

## Colors

| Token | Value | Used for |
|---|---|---|
| Navy | `#001F4B` | Hook text, logo and wordmark on light photos |
| White | `#FFFFFF` | Logo and wordmark on dark photos (dusk/night covers, e.g. page 23) |
| Sand | `#D9AD7F` at **77% opacity** | Hook box behind the text |

## Logo block (top centre)

- Orchid line icon, about **150 × 104 px**, top edge at about 5 px, centred.
- Wordmark **"Anggrek Permai"** below it as live text: serif, all caps, **32 px**, letter spacing −0.03, top at about 117 px. Together the block is about 274 px wide.
- Navy on light skies, white on dark skies.
- `editing/assets/logo-navy.png` and `logo-white.png` are transparent cut-outs of this block (icon + wordmark) from the 1080 px export. They're fine at this size; for anything bigger, export the icon from the design in Canva.

## Text on video (different from the covers)

Team rules, 2026-10-21. These are the **TikTok** rules; Instagram is calmer and more formal (see `docs/platform-strategy.md`).

- **Text on every screen.** Each shot keeps the previous text or shows a new short one; never a shot without text.
- **Short.** One or two short pieces of info at a time, a few words each. This applies to post captions too.
- **White on black** (TikTok-style box per line) or **black on white**. The sand box below is for thumbnails only, never on video.
- **Middle of the screen**, not at the bottom.
- **Emoji** in the text (🔑 🏡 😩 🔥 🛏️).
- **Phone number: green on white.**
- End card: logo, one offer, WhatsApp number. Nothing else.

## Hook box (thumbnails only)

- Rounded rectangle, **931 × 244 px**, at x 75 / y 334 (centred, upper third), corner radius about 37 px, sand `#D9AD7F` at 77% opacity.
- Text: **bold, 54–59 px, navy `#001F4B`, centred, line height 1.4**, two lines.
- Often ends with one emoji: 😆 ✨ ✅ 🫶 😍 🏡.

## Fonts

The connector returns Canva font IDs, not names. Visual matches for rendering outside Canva:

| Role | Canva font ID | Free match |
|---|---|---|
| Hook text | `YAFdJjbTu24` (bold) | **Poppins Bold** |
| Wordmark | `YACgEdeqDWI` | **Cinzel** (all-caps serif). Not needed when the logo PNG is used |

To confirm the exact names, open the design in Canva and click a text box; the font name shows in the toolbar.

## Background images

- Every cover uses a rendered image of the townhouse row (day, golden hour and dusk versions), not real photography.
- About 20 pages show a visible **"Canva" watermark** from unlicensed Pro images. Don't publish those pages as they are.
- For our videos, keep the cover layout but use **real footage** of the property underneath.

## Voice

Casual, upbeat Bahasa Indonesia aimed at young first-time buyers: kerja keras, sebelum nikah, sebelum 30, "bisa dong". The full hook list is in `docs/content-themes.md`.
