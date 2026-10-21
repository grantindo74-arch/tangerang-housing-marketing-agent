"""Render a 15s vertical video from a shot-list spec, in the AP Sosmed style.

Usage:
  python render.py specs/kunci-rumah.json --raw "G:/My Drive/Claude/Anggrek Permai/Raw video" --out ../drafts

Each spec lists shots (source clip, start, duration, optional text overlay) and
ends with an end card. Facts in overlay text ({cicilan}, {bedrooms}, ...) come
from config/approved-facts.json. Style follows docs/brand-style.md: logo block
top-centre as on the covers; on-video text is short, white on black (or black
on white) in the middle of the frame, with emoji; WhatsApp number green on white.
Needs ffmpeg/ffprobe on PATH (or --ffmpeg-dir) and Pillow.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
W, H, FPS = 1080, 1920, 30
COVER_TOP = (H - 1350) // 2  # top of the central 4:5 (1080x1350) cover area
NAVY, WHITE, BLACK = (0, 31, 75), (255, 255, 255), (0, 0, 0)
WA_GREEN = (18, 140, 62)  # darker WhatsApp green, readable on white
FONT_BOLD = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
FONT_SEMI = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.ttf")
FONT_EMOJI = "C:/Windows/Fonts/seguiemj.ttf"
FADE = 0.3  # crossfade length for transition "fade"

# On-video text styles (TikTok-native): text colour, box colour.
# The sand box from docs/brand-style.md is for thumbnails only, never on video.
STYLES = {
    "dark": (WHITE, BLACK + (230,)),   # white on black, the default
    "light": (BLACK, WHITE + (240,)),  # black on white
    "phone": (WA_GREEN, WHITE + (245,)),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2190 <= o <= 0x2BFF or o in (0x200D, 0xFE0F, 0x2122, 0x00A9)


def runs(text):
    """Split text into (is_emoji, chunk) runs so each gets the right font."""
    out = []
    for ch in text:
        e = is_emoji(ch)
        if out and out[-1][0] == e:
            out[-1][1] += ch
        else:
            out.append([e, ch])
    return out


def rich_width(draw, text, f, fe):
    return sum(draw.textlength(c, font=fe if e else f) for e, c in runs(text))


def draw_rich(draw, x, baseline, text, f, fe, fill):
    for e, chunk in runs(text):
        if e:
            draw.text((x, baseline), chunk, font=fe, anchor="ls", embedded_color=True)
            x += draw.textlength(chunk, font=fe)
        else:
            draw.text((x, baseline), chunk, font=f, anchor="ls", fill=fill)
            x += draw.textlength(chunk, font=f)


def text_lines(img, lines, center_y, style="dark", size=60):
    """TikTok-style caption: one rounded box per line, stacked, centred at center_y."""
    fg, bg = STYLES[style]
    f, fe = font(FONT_BOLD, size), font(FONT_EMOJI, int(size * 0.9))
    pad_x, line_h = int(size * 0.45), int(size * 1.5)
    top = int(center_y - line_h * len(lines) / 2)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, line in enumerate(lines):
        w = rich_width(d, line, f, fe)
        x0, y0 = (W - w) / 2 - pad_x, top + i * line_h
        d.rounded_rectangle((x0, y0, x0 + w + 2 * pad_x, y0 + line_h), int(size * 0.3), fill=bg)
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        w = rich_width(d, line, f, fe)
        draw_rich(d, (W - w) / 2, top + i * line_h + int(line_h * 0.7), line, f, fe, fg)


def overlay_png(kind, lines, path, y=None, style=None):
    """Text overlay for one shot, in the middle of the frame.

    kind is kept for older specs: "banner" defaults to the light style, the rest to dark.
    y: optional vertical centre as a fraction of frame height (default 0.5).
    """
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    style = style or ("light" if kind == "banner" else "dark")
    text_lines(img, lines, H * (y or 0.5), style, 64 if kind == "hook" else 56)
    img.save(path)


def logo_png(color, path, scale=1.0, top=None):
    """Logo block (icon + wordmark) top-centre, as on the covers."""
    logo = Image.open(os.path.join(ASSETS, f"logo-{color}.png"))
    if scale != 1.0:
        logo = logo.resize((round(logo.width * scale), round(logo.height * scale)), Image.LANCZOS)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(logo, ((W - logo.width) // 2, COVER_TOP + 8 if top is None else top))
    img.save(path)


def endcard_png(facts, offer, path):
    """Blurred-footage end card: logo, ONE short offer, WhatsApp number in the middle.

    Kept to a single fact on purpose: a 15s video leaves about 3s to read it.
    Offer is black on white; the phone number is green on white.
    """
    img = Image.new("RGBA", (W, H), NAVY + (170,))
    logo = Image.open(os.path.join(ASSETS, "logo-white.png"))
    logo = logo.resize((round(logo.width * 1.6), round(logo.height * 1.6)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - logo.width) // 2, int(H * 0.5) - 330))
    text_lines(img, [offer], H * 0.5 + 10, "light", 66)
    text_lines(img, ["WA " + facts["whatsapp"]], H * 0.5 + 150, "phone", 56)
    if "*" in offer:
        d = ImageDraw.Draw(img)
        f = font(FONT_SEMI, 28)
        t = facts["disclaimer"]
        d.text(((W - d.textlength(t, font=f)) / 2, H * 0.5 + 240), t, font=f, fill=(230, 233, 240))
    img.save(path)


def watermark_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 28)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((40, 120, 40 + tw + 36, 120 + 56), 14, fill=(200, 30, 40, 200))
    d.text((58, 158), text, font=f, fill=WHITE, anchor="ls")
    img.save(path)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def find_src(raw, name):
    for cand in (name, "Copy of " + name):
        p = os.path.join(raw, cand)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


BASE = ("scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1,"
        "eq=saturation={sat}:contrast=1.04").format(w=W, h=H, fps=FPS, sat="{sat}")


def render_shot(ff, src, start, dur, overlay, logo, out, sat, fade_from):
    """logo: static logo-block PNG (no fade) or None; overlay: text PNG that fades in."""
    frames = round(dur * FPS)
    base = BASE.format(sat=sat)
    cmd = [ff, "-y", "-ss", str(start), "-t", str(dur + 0.5), "-i", src]
    graph, last, idx = f"[0:v]{base}[v0]", "[v0]", 1
    if logo:
        cmd += ["-loop", "1", "-i", logo]
        graph += f";{last}[{idx}:v]overlay=0:0[v{idx}]"
        last, idx = f"[v{idx}]", idx + 1
    if overlay:
        cmd += ["-loop", "1", "-i", overlay]
        graph += (f";[{idx}:v]format=rgba,fade=t=in:st={fade_from}:d=0.25:alpha=1[o];"
                  f"{last}[o]overlay=0:0[v{idx}]")
        last = f"[v{idx}]"
    cmd += ["-filter_complex", graph + f";{last}format=yuv420p"]
    cmd += ["-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out]
    run(cmd)


def render_endcard(ff, bg_src, card, dur, out):
    frames = round(dur * FPS)
    run([ff, "-y", "-ss", "1.0", "-i", bg_src, "-loop", "1", "-i", card, "-filter_complex",
         f"[0:v]trim=end_frame=1,{BASE.format(sat=1.0)},boxblur=24:2,loop=loop=-1:size=1,"
         f"setpts=N/{FPS}/TB[bg];[1:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1[o];"
         f"[bg][o]overlay=0:0,format=yuv420p",
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--raw", required=True, help="folder with the raw clips")
    ap.add_argument("--out", required=True)
    ap.add_argument("--facts", default=os.path.join(HERE, "..", "config", "approved-facts.json"))
    ap.add_argument("--endcard-bg", default="IMG_1585.MOV")
    ap.add_argument("--ffmpeg-dir", default="")
    a = ap.parse_args()

    ff = os.path.join(a.ffmpeg_dir, "ffmpeg") if a.ffmpeg_dir else "ffmpeg"
    spec = json.load(open(a.spec, encoding="utf-8"))
    facts = json.load(open(a.facts, encoding="utf-8"))
    placeholder = not facts.get("_status", "").startswith("APPROVED")
    sat = 1.12 if spec["style"] == "A" else 1.05
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="render-")
    segs, durs = [], []
    try:
        for i, shot in enumerate(spec["shots"]):
            seg = os.path.join(tmp, f"seg{i:02d}.mp4")
            if shot.get("endcard"):
                card = os.path.join(tmp, "endcard.png")
                endcard_png(facts, shot.get("offer", "{cicilan}*").format(**facts), card)
                render_endcard(ff, find_src(a.raw, a.endcard_bg), card, shot["dur"], seg)
            else:
                ov = None
                if shot.get("text"):
                    ov = os.path.join(tmp, f"text{i:02d}.png")
                    lines = [l.format(**facts) for l in shot["text"]["lines"]]
                    overlay_png(shot["text"]["kind"], lines, ov, shot["text"].get("y"), shot["text"].get("style"))
                # Logo block per shot: spec default, overridable per shot ("navy", "white" or "none").
                color = shot.get("logo", spec.get("logo", "navy"))
                logo = None
                if color != "none":
                    logo = os.path.join(tmp, f"logo-{color}.png")
                    if not os.path.exists(logo):
                        logo_png(color, logo)
                fade_from = 0 if i == 0 else 0.2
                render_shot(ff, find_src(a.raw, shot["src"]), shot["start"], shot["dur"], ov, logo, seg, sat, fade_from)
            segs.append(seg)
            durs.append(shot["dur"])

        inputs = sum((["-i", s] for s in segs), [])
        n = len(segs)
        if spec["transition"] == "fade":
            chain, prev, t = [], "[0:v]", durs[0]
            for i in range(1, n):
                off = t - FADE
                chain.append(f"{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}]")
                prev, t = f"[x{i}]", off + durs[i]
            graph, total = ";".join(chain), t
        else:
            graph = "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[x{n - 1}]"
            prev, total = f"[x{n - 1}]", sum(durs)
        extra = 0
        if placeholder:
            wm = os.path.join(tmp, "wm.png")
            watermark_png("DRAFT · DATA CONTOH", wm)
            inputs += ["-loop", "1", "-i", wm]
            graph += f";{prev}[{n + extra}:v]overlay=0:0:shortest=1[wm]"
            prev, extra = "[wm]", extra + 1
        graph += f";{prev}null[vout]"
        out = os.path.join(a.out, spec["name"] + ".mp4")
        run([ff, "-y", *inputs, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
             "-filter_complex", graph, "-map", "[vout]", "-map", f"{n + extra}:a",
             "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
        print(f"{out}  {total:.1f}s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
