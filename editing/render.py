"""Render a vertical TikTok-style video from a shot-list spec.

Usage:
  python render.py specs/kunci-rumah.json --raw "G:/My Drive/Claude/Anggrek Permai/Raw video" --out ../drafts

The look follows the team's posted TikToks (docs/platform-strategy.md):
large navy logo top-centre on every shot; bold white outlined text in the
middle of the frame, with emoji; lines that build up shot by shot; a closing
call to action over the last real shots, with a white phone pill (green icon
and number) and a location line; quick flash cuts between some shots.

Spec format (JSON):
  name, transition ("cut" | "flash" | "fade", default for every join), logo ("navy" | "white"),
  shots: [{src, start, dur, ...one of:
      "text": {"lines": [...], "style": "outline" | "dark" | "light", "y": 0.44, "align": "center" | "left"}
              replace the text on screen (fades in)
      "add":  [...]            append lines under the current text (only the new lines fade in)
      "cta":  "Yuk, lihat unitnya langsung"   switch to the call to action (line + phone pill + location)
      nothing                  keep the previous shot's text (every screen carries text)
    optional "transition" (join into this shot), "logo": "none" | "navy" | "white"}]
  A legacy {"endcard": true, "dur": ..., "offer": ...} shot is still supported.
Facts in text ({cicilan_short}, {dp}, ...) come from config/approved-facts.json.
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
NAVY, WHITE, BLACK = (0, 31, 75), (255, 255, 255), (0, 0, 0)
WA_GREEN = (18, 140, 62)  # darker WhatsApp green, readable on white
WA_BADGE = (37, 180, 80)  # green circle behind the phone icon
FONT_BOLD = os.path.join(ASSETS, "fonts", "Poppins-Bold.ttf")
FONT_SEMI = os.path.join(ASSETS, "fonts", "Poppins-SemiBold.ttf")
FONT_EMOJI = "C:/Windows/Fonts/seguiemj.ttf"
FONT_ICONS = "C:/Windows/Fonts/segmdl2.ttf"  # Segoe MDL2 Assets, for the phone glyph
PHONE_GLYPH = "\uE717"

LOGO_WIDTH, LOGO_TOP = 486, 90  # about 45% of frame width, as in the posted TikToks
TEXT_TOP = 0.44                 # top of the text block, as a fraction of frame height
TEXT_SIZE = 60
TRANSITIONS = {"cut": ("fade", 1 / FPS), "flash": ("fadewhite", 0.25), "fade": ("fade", 0.3)}

# Box styles: text colour, box colour. "outline" (no box) is the default on video;
# the sand box from docs/brand-style.md is for thumbnails only.
STYLES = {
    "dark": (WHITE, BLACK + (230,)),
    "light": (BLACK, WHITE + (240,)),
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


def draw_rich(draw, x, baseline, text, f, fe, fill, stroke=0, stroke_fill=None):
    for e, chunk in runs(text):
        if e:
            draw.text((x, baseline), chunk, font=fe, anchor="ls", embedded_color=True)
            x += draw.textlength(chunk, font=fe)
        else:
            draw.text((x, baseline), chunk, font=f, anchor="ls", fill=fill,
                      stroke_width=stroke, stroke_fill=stroke_fill)
            x += draw.textlength(chunk, font=f)


def text_block(img, lines, top, style="outline", size=TEXT_SIZE, align="center", skip=0):
    """Draw a block of lines starting at `top`, one line per row.

    Positions depend only on the line index, so a block that grows shot by shot
    keeps earlier lines in place. `skip` leaves out the first lines (used to draw
    only the newly added ones). Returns the y just below the block.
    """
    f, fe = font(FONT_BOLD, size), font(FONT_EMOJI, int(size * 1.1))
    d = ImageDraw.Draw(img)
    widths = [rich_width(d, l, f, fe) for l in lines]
    line_h = int(size * (1.35 if style == "outline" else 1.5))
    left = (W - max(widths)) / 2 if widths else 0
    xs = [left if align == "left" else (W - w) / 2 for w in widths]
    shown = range(skip, len(lines))
    if style == "outline":
        # Soft drop shadow first, then white text with a dark outline.
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        for i in shown:
            draw_rich(sd, xs[i] + 3, top + i * line_h + int(line_h * 0.75) + 4, lines[i], f, fe,
                      (0, 0, 0, 150), stroke=size // 10, stroke_fill=(0, 0, 0, 150))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
        for i in shown:
            draw_rich(d, xs[i], top + i * line_h + int(line_h * 0.75), lines[i], f, fe,
                      WHITE, stroke=max(3, size // 14), stroke_fill=(0, 0, 0, 220))
    else:
        fg, bg = STYLES[style]
        pad_x = int(size * 0.45)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for i in shown:
            y0 = top + i * line_h
            ld.rounded_rectangle((xs[i] - pad_x, y0, xs[i] + widths[i] + pad_x, y0 + line_h),
                                 int(size * 0.3), fill=bg)
        img.alpha_composite(layer)
        for i in shown:
            draw_rich(d, xs[i], top + i * line_h + int(line_h * 0.7), lines[i], f, fe, fg)
    return top + len(lines) * line_h


def phone_pill(img, number, top):
    """White pill with a green phone badge on the left and the number in green."""
    f = font(FONT_BOLD, 54)
    d = ImageDraw.Draw(img)
    h = 104
    tw = d.textlength(number, font=f)
    w = h + 30 + tw + 50
    x0 = (W - w) / 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x0, top + 6, x0 + w, top + h + 6), h // 2, fill=(0, 0, 0, 90))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(8)))
    d.rounded_rectangle((x0, top, x0 + w, top + h), h // 2, fill=WHITE)
    d.rounded_rectangle((x0 - 6, top - 6, x0 + h + 6, top + h + 6), 30, fill=WA_BADGE)
    d.text((x0 + h / 2, top + h / 2), PHONE_GLYPH, font=font(FONT_ICONS, 52), fill=WHITE, anchor="mm")
    d.text((x0 + h + 30, top + h / 2), number, font=f, fill=WA_GREEN, anchor="lm")
    return top + h


def overlay_text(path, lines, style="outline", y=None, align="center", skip=0):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    text_block(img, lines, int(H * (y or TEXT_TOP)), style, TEXT_SIZE, align, skip)
    img.save(path)


def overlay_cta(path, line, facts, y=None, disclaimer=False):
    """Closing call to action: one line, the phone pill, a 📍 location line,
    and the small disclaimer when an earlier claim carried an asterisk."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bottom = text_block(img, [line], int(H * (y or TEXT_TOP)), "outline", 56)
    bottom = phone_pill(img, facts["whatsapp"], bottom + 16)
    bottom = text_block(img, ["\U0001F4CD " + facts["location"]], bottom + 18, "outline", 48)
    if disclaimer:
        text_block(img, [facts["disclaimer"]], bottom + 6, "outline", 30)
    img.save(path)


def logo_png(color, path):
    """Large logo block (icon + wordmark), top-centre."""
    logo = Image.open(os.path.join(ASSETS, f"logo-{color}.png"))
    scale = LOGO_WIDTH / logo.width
    logo = logo.resize((LOGO_WIDTH, round(logo.height * scale)), Image.LANCZOS)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(logo, ((W - logo.width) // 2, LOGO_TOP))
    img.save(path)


def endcard_png(facts, offer, path):
    """Legacy blurred-footage end card: logo, one offer, WhatsApp pill."""
    img = Image.new("RGBA", (W, H), NAVY + (170,))
    logo = Image.open(os.path.join(ASSETS, "logo-white.png"))
    logo = logo.resize((LOGO_WIDTH, round(logo.height * LOGO_WIDTH / logo.width)), Image.LANCZOS)
    img.alpha_composite(logo, ((W - logo.width) // 2, int(H * 0.5) - 360))
    bottom = text_block(img, [offer], int(H * 0.5) - 40, "light", 66)
    phone_pill(img, facts["whatsapp"], bottom + 30)
    img.save(path)


def watermark_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 28)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((40, 40, 40 + tw + 36, 40 + 56), 14, fill=(200, 30, 40, 200))
    d.text((58, 78), text, font=f, fill=WHITE, anchor="ls")
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


def render_shot(ff, src, start, dur, layers, out, sat):
    """layers: [(png, fade_from or None)], drawn in order; None means visible from the first frame."""
    frames = round(dur * FPS)
    cmd = [ff, "-y", "-ss", str(start), "-t", str(dur + 0.5), "-i", src]
    graph, last = f"[0:v]{BASE.format(sat=sat)}[v0]", "[v0]"
    for idx, (png, fade_from) in enumerate(layers, start=1):
        fade = "" if fade_from is None else f",fade=t=in:st={fade_from}:d=0.25:alpha=1"
        cmd += ["-loop", "1", "-i", png]
        graph += f";[{idx}:v]format=rgba{fade}[o{idx}];{last}[o{idx}]overlay=0:0[v{idx}]"
        last = f"[v{idx}]"
    cmd += ["-filter_complex", graph + f";{last}format=yuv420p",
            "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out]
    run(cmd)


def render_endcard(ff, bg_src, card, dur, out):
    frames = round(dur * FPS)
    run([ff, "-y", "-ss", "1.0", "-i", bg_src, "-loop", "1", "-i", card, "-filter_complex",
         f"[0:v]trim=end_frame=1,{BASE.format(sat=1.0)},boxblur=24:2,loop=loop=-1:size=1,"
         f"setpts=N/{FPS}/TB[bg];[1:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1[o];"
         f"[bg][o]overlay=0:0,format=yuv420p",
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "17", out])


def plan_text(spec, facts, tmp):
    """Work out the text layers for every shot.

    Returns one list per shot of (png, fade_from) pairs: what is already on
    screen (no fade) and what appears in this shot (fades in).
    """
    fill = lambda lines: [l.format(**facts) for l in lines]
    plans, lines, opts, current = [], [], {}, None
    starred = any("*" in l for s in spec["shots"] for l in s.get("text", {}).get("lines", []) + s.get("add", []))
    for i, shot in enumerate(spec["shots"]):
        appear = 0 if i == 0 else 0.15
        png = os.path.join(tmp, f"text{i:02d}.png")
        if shot.get("endcard"):
            plans.append([])
            continue
        if "text" in shot:
            t = shot["text"]
            lines = fill(t["lines"])
            opts = {"style": t.get("style", "outline"), "y": t.get("y"), "align": t.get("align", "center")}
            overlay_text(png, lines, **opts)
            current, layers = png, [(png, appear)]
        elif "add" in shot:
            if not lines:
                raise ValueError(f"shot {i}: 'add' needs text on screen first")
            new = os.path.join(tmp, f"new{i:02d}.png")
            old = len(lines)
            lines = lines + fill(shot["add"])
            overlay_text(new, lines, skip=old, **opts)
            overlay_text(png, lines, **opts)
            layers = [(current, None), (new, appear)]
            current = png
        elif "cta" in shot:
            overlay_cta(png, shot["cta"].format(**facts), facts, shot.get("y"), starred)
            current, layers, lines = png, [(png, appear)], []
        else:
            if current is None:
                raise ValueError("first shot needs text: every screen carries text")
            layers = [(current, None)]
        plans.append(layers)
    return plans


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
    sat = 1.12 if spec.get("style", "A") == "A" else 1.05
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="render-")
    segs, durs = [], []
    try:
        plans = plan_text(spec, facts, tmp)
        for i, (shot, layers) in enumerate(zip(spec["shots"], plans)):
            seg = os.path.join(tmp, f"seg{i:02d}.mp4")
            if shot.get("endcard"):
                card = os.path.join(tmp, "endcard.png")
                endcard_png(facts, shot.get("offer", "{cicilan_short}*").format(**facts), card)
                render_endcard(ff, find_src(a.raw, a.endcard_bg), card, shot["dur"], seg)
            else:
                # Logo block per shot: spec default, overridable per shot ("navy", "white" or "none").
                color = shot.get("logo", spec.get("logo", "navy"))
                if color != "none":
                    logo = os.path.join(tmp, f"logo-{color}.png")
                    if not os.path.exists(logo):
                        logo_png(color, logo)
                    layers = [(logo, None)] + layers
                render_shot(ff, find_src(a.raw, shot["src"]), shot["start"], shot["dur"], layers, seg, sat)
            segs.append(seg)
            durs.append(shot["dur"])

        # Join every segment with xfade; "cut" is a one-frame fade.
        inputs = sum((["-i", s] for s in segs), [])
        n = len(segs)
        chain, prev, t = [], "[0:v]", durs[0]
        for i in range(1, n):
            kind, dur = TRANSITIONS[spec["shots"][i].get("transition", spec.get("transition", "cut"))]
            off = t - dur
            chain.append(f"{prev}[{i}:v]xfade=transition={kind}:duration={dur:.3f}:offset={off:.3f}[x{i}]")
            prev, t = f"[x{i}]", off + durs[i]
        graph, total = ";".join(chain) if chain else "[0:v]null[x0]", t
        prev = prev if chain else "[x0]"
        extra = 0
        if placeholder:
            wm = os.path.join(tmp, "wm.png")
            watermark_png("DRAFT · DATA CONTOH", wm)
            inputs += ["-loop", "1", "-i", wm]
            graph += f";{prev}[{n}:v]overlay=0:0:shortest=1[wm]"
            prev, extra = "[wm]", 1
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
