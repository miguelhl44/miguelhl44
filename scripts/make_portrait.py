#!/usr/bin/env python3
"""Turn a photo into the animated ASCII portrait at the top of the README.

Run by hand, not by the daily workflow — the photo only changes when you
change it:

    python3 scripts/make_portrait.py            # rebuild portrait.svg
    python3 scripts/make_portrait.py --preview  # print it to the terminal

Needs Pillow, NumPy and fontTools (the daily stats script needs none of
these; keeping them here means the workflow stays dependency-free).

Two things make the result readable rather than mush:

  * The ramp is measured, not guessed. Every candidate glyph is rendered in
    the real typeface and ranked by how much ink it actually puts in its
    cell, so the steps are evenly spaced in tone. A hand-written ramp like
    " .:-=+*#@" assumes a coverage order the font may not honour.
  * The photo gets local contrast before sampling. This is a scanned print
    whose background (luminance 178-206) overlaps the lit cheek (168-182),
    so no global threshold can separate them; subtracting a heavy blur
    restores the local detail a plain autocontrast flattens.

The typeface is subset to just the ramp glyphs and inlined as base64. That
isn't decoration: an SVG loaded through <img> may not fetch subresources, so
a linked font would never arrive, and the grid assumes an advance width of
exactly 0.6 em — a viewer whose default monospace is narrower would see the
portrait squeezed. The subset costs about 2 KB.
"""
import argparse
import base64
import io
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TTF = os.path.join(HERE, "fonts", "JetBrainsMono-Regular.ttf")
SOURCE = os.path.join(HERE, "portrait-source.jpg")
OUT = os.path.join(ROOT, "portrait.svg")

# Glyphs allowed in the ramp: no XML metacharacters, nothing that reads as
# punctuation noise at 8px, and no space-lookalikes beyond the space itself.
CANDIDATES = " .':^~+-\\/|][)(tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

COLS = 72               # grid width in characters
CROP = (70, 0, 400, 424)  # source pixels: tighten onto head and shoulders
BLUR_FRAC = 0.09        # local-contrast radius, as a fraction of crop width
BLUR_AMOUNT = 1.1       # how much of the high-pass detail to add back
WHITE_POINT = 0.22      # ink below this is background: drop it to blank
GAMMA = 0.92            # <1 lifts the midtones the white point pulls down
VIGNETTE = (0.82, 1.30) # normalised radii: fully opaque -> fully faded
LEVELS = 11             # ramp steps

FS = 8.0                # font size, px
LH = 8.0                # line height, px — tight, so cells stay square-ish
ADV = 0.6               # JetBrains Mono advance width, em
PAD = 6.0
ROW_DUR = 0.09          # one row's wipe
ROW_STEP = 0.042        # stagger between rows
ROW_FADE = 0.55         # each row keeps easing up long after its wipe lands,
                        # so a soft band travels down the image instead of
                        # rows snapping on one at a time

INK_LIGHT, INK_DARK = "#30363d", "#c9d1d9"
CURSOR = "#2da44e"


# ---------------------------------------------------------------- ramp

def measure_coverage(px=64):
    """Ink coverage of each candidate glyph in its own cell, 0..1."""
    font = ImageFont.truetype(TTF, px)
    cell = (max(int(round(font.getlength("M"))), 1), px)
    out = {}
    for ch in CANDIDATES:
        img = Image.new("L", cell, 0)
        ImageDraw.Draw(img).text((0, 0), ch, fill=255, font=font, anchor="la")
        out[ch] = sum(img.getdata()) / (255.0 * cell[0] * cell[1])
    return out


def build_ramp(coverage, levels):
    """Glyphs whose measured coverage is as evenly spaced as possible."""
    ranked = sorted(coverage.items(), key=lambda kv: kv[1])
    lo, hi = ranked[0][1], ranked[-1][1]
    ramp = []
    for i in range(levels):
        target = lo + (hi - lo) * i / (levels - 1)
        ch = min(ranked, key=lambda kv: abs(kv[1] - target))[0]
        if not ramp or ch != ramp[-1]:
            ramp.append(ch)
    return "".join(ramp)


# ---------------------------------------------------------------- image

def vignette_mask(shape, inner, outer):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    return np.clip((outer - r) / (outer - inner), 0.0, 1.0)


def to_grid(path, ramp):
    """Sample the photo into a grid of ramp indices, densest = darkest."""
    im = Image.open(path).convert("L").crop(CROP)
    a = np.asarray(im, dtype=float)

    radius = max(a.shape[1] * BLUR_FRAC, 1.0)
    blur = np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=float)
    a = np.clip(a + (a - blur) * BLUR_AMOUNT, 0, 255)
    a = (a - a.min()) / max(a.max() - a.min(), 1.0)

    rows = max(1, int(round(COLS * (a.shape[0] / a.shape[1]) * ADV)))
    small = np.asarray(
        Image.fromarray((a * 255).astype(np.uint8))
             .resize((COLS, rows), Image.LANCZOS), dtype=float) / 255.0

    ink = 1.0 - small                                    # 1 = darkest
    ink = np.clip((ink - WHITE_POINT) / (1.0 - WHITE_POINT), 0.0, 1.0)
    ink = ink ** GAMMA
    ink *= vignette_mask(ink.shape, *VIGNETTE)
    return np.rint(ink * (len(ramp) - 1)).astype(int)


# ---------------------------------------------------------------- font

def subset_font(chars):
    """JetBrains Mono cut down to `chars`, as WOFF (no brotli needed)."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(TTF)
    options = subset.Options(desubroutinize=True, notdef_outline=False)
    options.layout_features = []
    options.name_IDs = []
    options.drop_tables += ["GSUB", "GPOS", "GDEF", "kern"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(set(chars))))
    subsetter.subset(font)
    font.flavor = "woff"
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------- svg

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(grid, ramp, woff):
    rows, cols = grid.shape
    cw = FS * ADV
    width = round(PAD * 2 + cols * cw, 1)
    height = round(PAD * 2 + rows * LH, 1)
    b64 = base64.b64encode(woff).decode("ascii")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="JBMonoRamp,ui-monospace,SFMono-Regular,Menlo,'
        f'Consolas,monospace" font-size="{FS}">'
        f"<style>@font-face{{font-family:JBMonoRamp;font-style:normal;"
        f"font-weight:400;font-display:block;"
        f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        f".i{{fill:{INK_LIGHT}}}.c{{fill:{CURSOR}}}"
        f"@media(prefers-color-scheme:dark){{.i{{fill:{INK_DARK}}}}}"
        f"</style>"
    ]

    for r in range(rows):
        line = "".join(ramp[i] for i in grid[r]).rstrip()
        if not line:
            continue
        begin = r * ROW_STEP
        w_px = len(line) * cw
        y_top = PAD + r * LH
        baseline = y_top + FS * 0.78
        cid = f"r{r}"
        out.append(
            f'<clipPath id="{cid}"><rect x="{PAD}" y="{y_top:.1f}" '
            f'width="0" height="{LH}">'
            f'<animate attributeName="width" from="0" to="{w_px:.1f}" '
            f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f"</rect></clipPath>"
            f'<g opacity="0" clip-path="url(#{cid})">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.2f}s" dur="{ROW_FADE}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.3 0.7 0.3 1" '
            f'keyTimes="0;1" values="0;1"/>'
            f'<text x="{PAD}" y="{baseline:.1f}" class="i" '
            f'xml:space="preserve">{esc(line)}</text></g>'
            f'<rect x="{PAD}" y="{y_top:.1f}" width="{cw:.1f}" '
            f'height="{LH}" class="c" opacity="0">'
            f'<set attributeName="opacity" to="0.55" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{PAD}" '
            f'to="{PAD + w_px:.1f}" begin="{begin:.2f}s" dur="{ROW_DUR}s" '
            f'fill="freeze"/>'
            f'<animate attributeName="opacity" from="0.55" to="0" '
            f'begin="{begin + ROW_DUR:.2f}s" dur="0.18s" fill="freeze"/>'
            f"</rect>"
        )
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=SOURCE, help="photo to convert")
    ap.add_argument("--out", default=OUT, help="svg to write")
    ap.add_argument("--preview", action="store_true",
                    help="print the grid instead of writing the svg")
    args = ap.parse_args()

    ramp = build_ramp(measure_coverage(), LEVELS)
    grid = to_grid(args.source, ramp)

    if args.preview:
        print(f"ramp {ramp!r}  grid {grid.shape[1]}x{grid.shape[0]}")
        for row in grid:
            print("".join(ramp[i] for i in row).rstrip())
        return

    svg = build_svg(grid, ramp, subset_font(ramp))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    rows = grid.shape[0]
    print(f"{args.out}: {grid.shape[1]}x{rows} chars, ramp {ramp!r}, "
          f"{len(svg) / 1024:.1f} KB, "
          f"reveal {rows * ROW_STEP + ROW_DUR:.1f}s")


if __name__ == "__main__":
    main()
