#!/usr/bin/env python3
"""
Perpetual Motion Instagram graphic generator.

Usage:
  python3 generate.py spec.json out_dir

spec.json:
{
  "slug": "2026-09-28-sleep-anchor",      # file prefix, lowercase, hyphens
  "slides": [                              # 1 slide = single post; 2+ = carousel
    {"kicker": "HEALTH COACHING",          # small label above headline (optional)
     "headline": "Protect the first hour after you wake up.",
     "body": "Optional supporting line or two. Keep it short."},   # optional
    ...
  ]
}

Output: 1080x1350 JPEGs (4:5 portrait, Instagram feed max height) named
<slug>-01.jpg, <slug>-02.jpg ... plus <slug>-cover.jpg (1080x1920) for Reels
when the spec has "reel_cover": {"headline": "..."}.

Design: dark, premium, calm. Near-black background with a faint purple
gradient, off-white Poppins type, one thin magenta accent rule, small
PERPETUAL MOTION wordmark. No icons, no photos, no clutter.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
FONTS = {
    "bold": os.path.join(FONT_DIR, "Poppins-Bold.ttf"),
    "medium": os.path.join(FONT_DIR, "Poppins-Medium.ttf"),
    "regular": os.path.join(FONT_DIR, "Poppins-Regular.ttf"),
    "light": os.path.join(FONT_DIR, "Poppins-Light.ttf"),
}
BG = (13, 12, 18)
INK = (242, 240, 246)
MUTED = (168, 164, 180)
ACCENT = (172, 58, 190)      # magenta-purple, matches the site accent
GLOW = (92, 40, 120)

def font(kind, size):
    return ImageFont.truetype(FONTS[kind], size)

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def background(W, H):
    img = Image.new("RGB", (W, H), BG)
    # soft purple glow, bottom-right, blurred so it reads as depth not decoration
    glow = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(glow)
    g.ellipse([W*0.45, H*0.55, W*1.35, H*1.45], fill=GLOW)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    img = Image.blend(img, glow, 0.55)
    # faint grain for a printed, non-digital feel
    return img

def fit_headline(draw, text, max_w, max_h, start=88, floor=54):
    size = start
    while size >= floor:
        f = font("bold", size)
        lines = wrap(draw, text, f, max_w)
        lh = int(size * 1.12)
        if len(lines) * lh <= max_h:
            return f, lines, lh
        size -= 4
    f = font("bold", floor)
    return f, wrap(draw, text, f, max_w), int(floor * 1.12)

def render_slide(slide, idx, total, W=1080, H=1350):
    img = background(W, H)
    d = ImageDraw.Draw(img)
    M = 96                       # margin
    max_w = W - 2*M

    kicker = slide.get("kicker")
    body = slide.get("body")
    head_budget = H*0.42 if body else H*0.5
    f, lines, lh = fit_headline(d, slide["headline"], max_w, head_budget)
    bf = font("light", 36)
    body_lines = wrap(d, body, bf, max_w) if body else []

    # measure the block, then center it slightly above the optical middle
    block = (70 if kicker else 0) + 56 + len(lines)*lh + (40 + len(body_lines)*52 if body else 0)
    y = max(150, int((H - 120 - block) * 0.42))

    if kicker:
        d.text((M, y), kicker.upper(), font=font("medium", 26), fill=ACCENT, spacing=4)
        y += 70

    # accent rule
    d.rectangle([M, y, M+120, y+4], fill=ACCENT)
    y += 56

    for ln in lines:
        d.text((M, y), ln, font=f, fill=INK)
        y += lh
    y += 40

    for ln in body_lines:
        d.text((M, y), ln, font=bf, fill=MUTED)
        y += 52

    # footer: wordmark left, slide counter right
    fy = H - 120
    d.text((M, fy), "PERPETUAL MOTION", font=font("medium", 24), fill=MUTED, spacing=6)
    if total > 1:
        counter = f"{idx:02d} / {total:02d}"
        cf = font("regular", 24)
        d.text((W - M - d.textlength(counter, font=cf), fy), counter, font=cf, fill=MUTED)
        if idx < total:
            hint = "swipe"
            hf = font("light", 22)
            d.text((W - M - d.textlength(hint, font=hf), fy + 36), hint, font=hf, fill=ACCENT)
    return img

def render_cover(spec, W=1080, H=1920):
    img = background(W, H)
    d = ImageDraw.Draw(img)
    M = 100
    y = 640
    d.rectangle([M, y, M+120, y+4], fill=ACCENT); y += 60
    f, lines, lh = fit_headline(d, spec["reel_cover"]["headline"], W-2*M, 600, start=96, floor=60)
    for ln in lines:
        d.text((M, y), ln, font=f, fill=INK); y += lh
    d.text((M, H-200), "PERPETUAL MOTION", font=font("medium", 26), fill=MUTED, spacing=6)
    return img

def save(img, path, compact):
    """Default: gradient JPEG (~60-85KB). Compact: flat-background 48-color PNG
    (~20KB), used when the image must travel as base64 through a tool call."""
    if compact:
        img.quantize(16, dither=Image.Dither.NONE).save(path, optimize=True)
        try:  # zopfli recompression, ~25% smaller (pip install pyoxipng)
            import oxipng
            oxipng.optimize(path, path, level=6, deflate=oxipng.Deflaters.zopfli(15))
        except ImportError:
            pass
    else:
        img.save(path, quality=88, optimize=True)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    compact = "--compact" in sys.argv
    spec = json.load(open(args[0]))
    out = args[1]
    os.makedirs(out, exist_ok=True)
    if compact:
        global background
        background = lambda W, H: Image.new("RGB", (W, H), BG)
    ext = "png" if compact else "jpg"
    slug = spec["slug"]
    slides = spec.get("slides", [])
    written = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(out, f"{slug}-{i:02d}.{ext}")
        save(render_slide(s, i, len(slides)), p, compact)
        written.append(p)
    if spec.get("reel_cover"):
        p = os.path.join(out, f"{slug}-cover.{ext}")
        save(render_cover(spec), p, compact)
        written.append(p)
    for p in written:
        print(p, os.path.getsize(p))

if __name__ == "__main__":
    main()
