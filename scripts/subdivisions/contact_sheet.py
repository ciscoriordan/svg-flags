#!/usr/bin/env python3
"""Render review sheets of the built flags into .cache/subdivisions/sheets/.

One sheet per country. Each row shows the full-size flag, the circle and the
square at 96 px, the circle as CoreSVG draws it (macOS only), and the circle
at 24 px (a typical list-row size) on a light and on a dark background. Crops,
zoom and border choices are approved by eye from these sheets.

Usage: contact_sheet.py [CODE or COUNTRY ...]
"""

import sys
import tempfile
from pathlib import Path

from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from common import CACHE, REPO, coresvg_available, coresvg_render, load_flags, render, select_codes

ROW = 96
SMALL = 24
LIGHT = (255, 255, 255)
DARK = (28, 28, 30)
FONT_PATHS = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(size):
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def on(background, image):
    base = Image.new("RGBA", image.size, background + (255,))
    base.alpha_composite(image)
    return base.convert("RGB")


def row(code, name, core_png):
    full_path = REPO / "full-size" / "states" / f"{code}.svg"
    root = etree.parse(str(full_path)).getroot()
    full = render(full_path, round(ROW * float(root.get("width")) / float(root.get("height"))), ROW)
    circle = render(REPO / "circle" / "states" / f"{code}.svg", ROW, ROW)
    square = render(REPO / "square" / "states" / f"{code}.svg", ROW, ROW)
    small = render(REPO / "circle" / "states" / f"{code}.svg", SMALL * 2, SMALL * 2).resize((SMALL, SMALL), Image.LANCZOS)
    tiles = [on(LIGHT, full), on((200, 200, 200), circle), on((200, 200, 200), square)]
    if core_png and core_png.exists():
        tiles.append(on((200, 200, 200), Image.open(core_png).convert("RGBA")))
    light = Image.new("RGB", (ROW // 2, ROW), LIGHT)
    light.paste(on(LIGHT, small), ((ROW // 2 - SMALL) // 2, (ROW - SMALL) // 2))
    dark = Image.new("RGB", (ROW // 2, ROW), DARK)
    dark.paste(on(DARK, small), ((ROW // 2 - SMALL) // 2, (ROW - SMALL) // 2))
    tiles += [light, dark]
    width = 300 + sum(t.width + 10 for t in tiles) + 10
    out = Image.new("RGB", (max(width, 1100), ROW + 10), LIGHT)
    draw = ImageDraw.Draw(out)
    draw.text((10, ROW // 2 - 18), code, fill=(0, 0, 0), font=font(18))
    draw.text((10, ROW // 2 + 4), name, fill=(90, 90, 90), font=font(14))
    x = 300
    for tile in tiles:
        out.paste(tile, (x, 5))
        x += tile.width + 10
    return out


def main():
    data = load_flags()
    flags = data["flags"]
    codes = [c for c in select_codes(sys.argv[1:], flags) if (REPO / "circle" / "states" / f"{c}.svg").exists()]
    out_dir = CACHE / "sheets"
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        core = {}
        if coresvg_available():
            jobs = [(REPO / "circle" / "states" / f"{c}.svg", Path(tmp) / f"{c}.png", ROW, ROW) for c in codes]
            coresvg_render(jobs)
            core = {c: Path(tmp) / f"{c}.png" for c in codes}
        for country in sorted({c.split("-")[0] for c in codes}):
            rows = [row(c, flags[c]["name"], core.get(c)) for c in codes if c.startswith(country + "-")]
            sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), LIGHT)
            y = 0
            for r in rows:
                sheet.paste(r, (0, y))
                y += r.height
            path = out_dir / f"{country}.png"
            sheet.save(path)
            print(path.relative_to(REPO))


if __name__ == "__main__":
    main()
