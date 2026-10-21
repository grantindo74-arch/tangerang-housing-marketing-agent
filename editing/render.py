"""Render a 15s vertical video from a shot-list spec, in the AP Sosmed style.

Usage:
  python render.py specs/kunci-rumah.json --raw "G:/My Drive/Claude/Anggrek Permai/Raw video" --out ../drafts

Each spec lists shots (source clip, start, duration, optional text overlay) and
ends with an end card. Facts in overlay text ({cicilan}, {bedrooms}, ...) come
from config/approved-facts.json. Style follows docs/brand-style.md: logo block
top-centre, sand hook box with navy Poppins Bold, layout kept inside the
central 4:5 area so it matches the TikTok covers.
Needs ffmpeg/ffprobe on PATH (or --ffmpeg-dir) and Pillow.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
W, H, FPS = 1080, 1920, 30
COVER_TOP = (H - 1350) // 2  # top of the central 4:5 (1080x1350) cover area
NAVY, WHITE = (0, 31, 75), (255, 255, 255)
SAND = (217, 173, 127, 196)  # #D9AD7F at 77%
FONT_BOLD = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
FONT_SEMI = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.ttf")
FADE = 0.3  # crossfade length for transition "fade"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_box(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0], box[1]


def rounded_box(img, xy, radius, fill, shadow=True):
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        x0, y0, x1, y1 = xy
        ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 8, x1, y1 + 8), radius, fill=(0, 0, 0, 70))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(xy, radius, fill=fill)
    img.alpha_composite(layer)


def centered_lines(img, lines, f, top, fill, line_h):
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        w, oy = text_box(d, line, f)
        d.text(((W - w) // 2, top + i * line_h - oy), line, font=f, fill=fill)


def overlay_png(kind, lines, path, y=None):
    """Text overlay for one shot.

    hook:   the cover's sand box (931 px wide, upper third of the 4:5 area).
    label:  a smaller sand box lower in frame, for room names and features.
    banner: navy box with white text, for price and cicilan lines.
    y: optional top of the box as a fraction of frame height.
    """
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if kind == "hook":
        f = font(FONT_BOLD, 58 if max(len(l) for l in lines) <= 26 else 50)
        lh = int(f.size * 1.4)
        box_h = max(244, lh * len(lines) + 70)
        top = int(H * y) if y else COVER_TOP + 334
        rounded_box(img, (75, top, 75 + 931, top + box_h), 37, SAND)
        centered_lines(img, lines, f, top + (box_h - lh * len(lines)) // 2 + int(f.size * 0.2), NAVY, lh)
    else:
        f = font(FONT_BOLD, 48)
        fg, bg = (NAVY, SAND) if kind == "label" else (WHITE, NAVY + (235,))
        lh = int(f.size * 1.4)
        d = ImageDraw.Draw(img)
        box_w = max(text_box(d, l, f)[0] for l in lines) + 96
        box_h = lh * len(lines) + 44
        top = int(H * y) if y else COVER_TOP + 1350 - 190 - box_h
        x0 = (W - box_w) // 2
        rounded_box(img, (x0, top, x0 + box_w, top + box_h), 30, bg)
        centered_lines(img, lines, f, top + 22 + int(f.size * 0.2), fg, lh)
    img.save(path)


def logo_png(color, path, scale=1.0, top=None):
    """Logo block (icon + wordmark) top-centre, as on the covers."""
    logo = Image.open(os.path.join(ASSETS, f"logo-{color}.png"))
    if scale != 1.0:
        logo = logo.resize((round(logo.width * scale), round(logo.height * scale)), Image.LANCZOS)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(logo, ((W - logo.width) // 2, COVER_TOP + 8 if top is None else top))
    img.save(path)


def endcard_png(facts, path):
    """Blurred-footage end card: logo, offer box in sand, WhatsApp line."""
    img = Image.new("RGBA", (W, H), NAVY + (190,))
    logo = Image.open(os.path.join(ASSETS, "logo-white.png"))
    logo = logo.resize((round(logo.width * 1.6), round(logo.height * 1.6)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - logo.width) // 2, 420))
    f_sub = font(FONT_SEMI, 46)
    centered_lines(img, [facts["unit"], facts["city"]], f_sub, 680, WHITE, 66)

    offer = [facts["price"] + "*", facts["dp"] + " · " + facts["cicilan"] + "*"]
    f_offer = font(FONT_BOLD, 44)
    lh = int(f_offer.size * 1.45)
    top, box_h = 860, lh * len(offer) + 70
    rounded_box(img, (75, top, 75 + 931, top + box_h), 37, SAND[:3] + (235,))
    centered_lines(img, offer, f_offer, top + 35 + int(f_offer.size * 0.2), NAVY, lh)

    f_wa = font(FONT_BOLD, 56)
    centered_lines(img, ["WhatsApp " + facts["whatsapp"]], f_wa, top + box_h + 70, WHITE, 70)
    centered_lines(img, [facts["disclaimer"]], font(FONT_SEMI, 30), top + box_h + 170, (225, 230, 240), 40)
    img.save(path)


def watermark_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 28)
    tw, oy = text_box(d, text, f)
    d.rounded_rectangle((40, 120, 40 + tw + 36, 120 + 56), 14, fill=(200, 30, 40, 200))
    d.text((58, 132 - oy), text, font=f, fill=WHITE)
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
                endcard_png(facts, card)
                render_endcard(ff, find_src(a.raw, a.endcard_bg), card, shot["dur"], seg)
            else:
                ov = None
                if shot.get("text"):
                    ov = os.path.join(tmp, f"text{i:02d}.png")
                    lines = [l.format(**facts) for l in shot["text"]["lines"]]
                    overlay_png(shot["text"]["kind"], lines, ov, shot["text"].get("y"))
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
