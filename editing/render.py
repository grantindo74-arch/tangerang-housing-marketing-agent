"""Render a 15s vertical draft video from a shot-list spec.

Usage:
  python render.py specs/kunci-rumah.json --raw "G:/My Drive/Claude/Anggrek Permai/Raw video" --out ../drafts

Each spec lists shots (source clip, start, duration, optional text overlay) and
ends with an end card. Facts in overlay text ({cicilan}, {bedrooms}, ...) are
filled from a facts file (placeholder-facts.json until the approved facts exist).
Needs ffmpeg/ffprobe on PATH (or --ffmpeg-dir) and Pillow.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
NAVY, YELLOW, WHITE = (20, 36, 66), (255, 199, 44), (255, 255, 255)
FONT_BLACK = "C:/Windows/Fonts/seguibl.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"
FADE = 0.3  # crossfade length for style B


def font(path, size):
    return ImageFont.truetype(path, size)


def text_size(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0], box[3] - box[1], box[1]


def shadowed(img, draw_fn, blur=10, opacity=150):
    """Draw text twice: a blurred dark copy for legibility, then the real one."""
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(shadow), (0, 0, 0, opacity), offset=4)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))
    draw_fn(ImageDraw.Draw(img), None, offset=0)


def overlay_png(kind, lines, path, y=None):
    """y: vertical centre of the text as a fraction of frame height (hook only)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "hook":
        f = font(FONT_BLACK, 92 if max(len(l) for l in lines) <= 18 else 76)
        lh = int(f.size * 1.18)
        top = int(H * (y or 0.25)) - lh * len(lines) // 2

        def draw(dr, color, offset):
            for i, line in enumerate(lines):
                w, _, _ = text_size(dr, line, f)
                xy = ((W - w) // 2 + offset, top + i * lh + offset)
                if color:
                    dr.text(xy, line, font=f, fill=color)
                else:
                    dr.text(xy, line, font=f, fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0, 90))
        shadowed(img, draw, blur=14, opacity=170)
    elif kind in ("label", "banner"):
        f = font(FONT_BOLD if kind == "label" else FONT_BLACK, 54 if kind == "label" else 60)
        fg, bg = (NAVY, YELLOW) if kind == "label" else (YELLOW, NAVY + (235,))
        lh = int(f.size * 1.25)
        widths = [text_size(d, l, f)[0] for l in lines]
        pad_x, pad_y = 34, 22
        box_w = max(widths) + pad_x * 2
        box_h = lh * len(lines) + pad_y * 2 - (lh - f.size)
        x = 64 if kind == "label" else (W - box_w) // 2
        y = int(H * 0.64)
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x + 4, y + 8, x + box_w + 4, y + box_h + 8), 22, fill=(0, 0, 0, 110))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d.rounded_rectangle((x, y, x + box_w, y + box_h), 22, fill=bg)
        for i, line in enumerate(lines):
            _, _, oy = text_size(d, line, f)
            d.text((x + pad_x, y + pad_y + i * lh - oy), line, font=f, fill=fg)
    img.save(path)


def endcard_png(facts, path):
    img = Image.new("RGBA", (W, H), NAVY + (215,))
    d = ImageDraw.Draw(img)

    def center(text, f, y, fill, spacing=0):
        if spacing:
            widths = [text_size(d, c, f)[0] for c in text]
            total = sum(widths) + spacing * (len(text) - 1)
            x = (W - total) // 2
            for c, w in zip(text, widths):
                d.text((x, y), c, font=f, fill=fill)
                x += w + spacing
        else:
            w, _, _ = text_size(d, text, f)
            d.text(((W - w) // 2, y), text, font=f, fill=fill)

    y = 560
    center(facts["brand"].upper(), font(FONT_BLACK, 104), y, WHITE)
    center(facts["city"].upper(), font(FONT_BOLD, 46), y + 150, YELLOW, spacing=14)
    d.line((W // 2 - 90, y + 250, W // 2 + 90, y + 250), fill=YELLOW, width=5)
    center(facts["unit"], font(FONT_SEMI, 52), y + 290, WHITE)
    f = font(FONT_BLACK, 56)
    label = facts["cicilan"] + "*"
    tw, _, oy = text_size(d, label, f)
    bx, by = (W - tw - 70) // 2, y + 400
    d.rounded_rectangle((bx, by, bx + tw + 70, by + 104), 26, fill=YELLOW)
    d.text((bx + 35, by + 22 - oy), label, font=f, fill=NAVY)
    center("WhatsApp " + facts["whatsapp"], font(FONT_BOLD, 54), y + 570, WHITE)
    center(facts["disclaimer"], font(FONT_SEMI, 32), y + 660, (220, 225, 235))
    img.save(path)


def watermark_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(FONT_BOLD, 30)
    tw, th, oy = text_size(d, text, f)
    d.rounded_rectangle((40, 150, 40 + tw + 36, 150 + th + 24), 14, fill=(200, 30, 40, 200))
    d.text((58, 162 - oy), text, font=f, fill=WHITE)
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


def render_shot(ff, src, start, dur, overlay, out, sat, fade_from):
    frames = round(dur * FPS)
    base = BASE.format(sat=sat)
    cmd = [ff, "-y", "-ss", str(start), "-t", str(dur + 0.5), "-i", src]
    if overlay:
        cmd += ["-loop", "1", "-i", overlay,
                "-filter_complex",
                f"[0:v]{base}[v];[1:v]format=rgba,fade=t=in:st={fade_from}:d=0.25:alpha=1[o];"
                f"[v][o]overlay=0:0,format=yuv420p"]
    else:
        cmd += ["-vf", base + ",format=yuv420p"]
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
    ap.add_argument("--facts", default=os.path.join(os.path.dirname(__file__), "placeholder-facts.json"))
    ap.add_argument("--endcard-bg", default="IMG_1585.MOV")
    ap.add_argument("--ffmpeg-dir", default="")
    ap.add_argument("--no-watermark", action="store_true")
    a = ap.parse_args()

    ff = os.path.join(a.ffmpeg_dir, "ffmpeg") if a.ffmpeg_dir else "ffmpeg"
    spec = json.load(open(a.spec, encoding="utf-8"))
    facts = json.load(open(a.facts, encoding="utf-8"))
    placeholder = "PLACEHOLDER" in facts.get("_status", "")
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
                fade_from = 0 if i == 0 else 0.2
                render_shot(ff, find_src(a.raw, shot["src"]), shot["start"], shot["dur"], ov, seg, sat, fade_from)
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
        audio_idx = n
        if placeholder and not a.no_watermark:
            wm = os.path.join(tmp, "wm.png")
            watermark_png("DRAFT · DATA CONTOH", wm)
            inputs += ["-loop", "1", "-i", wm]
            graph += f";{prev}[{n}:v]overlay=0:0:shortest=1[vout]"
            audio_idx += 1
        else:
            graph += f";{prev}null[vout]"
        out = os.path.join(a.out, spec["name"] + ".mp4")
        run([ff, "-y", *inputs, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
             "-filter_complex", graph, "-map", "[vout]", "-map", f"{audio_idx}:a",
             "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out])
        print(f"{out}  {total:.1f}s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
