#!/usr/bin/env python3
"""Measure where an emblem sits on a flag, in the flag units that recipes use.

Renders the cleaned full-size flag and prints the bounding box of every pixel
that differs from the given background colors, optionally inside a region.
The result goes into a recipe as "fit": [x, y, width, height], or as the
"from" rectangle of a layer.

Example: the badge on the fly half of Ontario's red ensign
    measure.py ca-on --region 1 0 1 1 --background "#D80621"

Usage: measure.py CODE [--region X Y W H] [--background COLOR ...]
"""

import argparse

from lxml import etree

import svgtools as st
from common import cleaned_path, render

RESOLUTION = 1000  # pixels per flag unit


def hex_rgb(color):
    color = st.normalize_color(color).lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("code")
    parser.add_argument("--region", nargs=4, type=float, metavar=("X", "Y", "W", "H"))
    parser.add_argument("--background", nargs="*", default=["#FFFFFF"])
    parser.add_argument("--tolerance", type=int, default=24, help="per-channel distance still counted as background")
    args = parser.parse_args()

    root = etree.parse(str(cleaned_path(args.code))).getroot()
    vb = st.viewbox(root)
    unit = min(vb[2], vb[3])
    width, height = round(vb[2] / unit * RESOLUTION), round(vb[3] / unit * RESOLUTION)
    image = render(cleaned_path(args.code), width, height)
    backgrounds = [hex_rgb(c) for c in args.background]

    x0, y0, w, h = args.region or (0, 0, vb[2] / unit, vb[3] / unit)
    left, top = round(x0 * RESOLUTION), round(y0 * RESOLUTION)
    right, bottom = round((x0 + w) * RESOLUTION), round((y0 + h) * RESOLUTION)
    px = image.load()
    box = None
    for y in range(max(0, top), min(height, bottom)):
        for x in range(max(0, left), min(width, right)):
            r, g, b, a = px[x, y]
            if a < 128 or any(max(abs(r - c[0]), abs(g - c[1]), abs(b - c[2])) <= args.tolerance for c in backgrounds):
                continue
            box = [x, y, x, y] if box is None else [min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)]
    if box is None:
        print("nothing but background in that region")
        return
    bx, by = box[0] / RESOLUTION, box[1] / RESOLUTION
    bw, bh = (box[2] + 1 - box[0]) / RESOLUTION, (box[3] + 1 - box[1]) / RESOLUTION
    print(f"flag {vb[2] / unit:.3f} x {vb[3] / unit:.3f} units")
    print(f'"fit": [{bx:.3f}, {by:.3f}, {bw:.3f}, {bh:.3f}]')


if __name__ == "__main__":
    main()
