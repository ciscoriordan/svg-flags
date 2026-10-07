#!/usr/bin/env python3
"""Build circle/states and square/states from the cleaned full-size art.

Each variant is a 512x512 composition of the full-size drawing, placed by the
"layout" recipe in flags.json. Lengths in a recipe are in flag units: 1.0 is
the shorter side of the flag, measured from the top-left of its viewBox. So
on a 2:1 flag the whole flag is 2.0 wide and 1.0 tall.

  "crop": "center" | "hoist" | "fly" | "top" | "bottom"
      A square window as tall as the flag (as wide, for portrait flags),
      centered, at the hoist (left) or at the fly (right). Default: center.
  "window": [x, y, side]
      An explicit square window, for emblems that are not centered.
  "fit": [x, y, width, height], "fill": share
      Center the window on an emblem (measured with measure.py) and size it
      so the emblem's longer side spans that share of the output (default
      0.85). Used for coats of arms on a plain field.
  "zoom": z
      Scale the window about its center; z < 1 shows more of the flag.
  "fills": [["#RRGGBB", x, y, width, height], ...]
      Solid rectangles in the 512 output space, drawn first. Used where a
      zoomed-out window runs past the edge of the flag, and for layouts
      assembled from parts. The colors must be colors of the flag.
  "covers": [["#RRGGBB", x, y, width, height], ...]
      Like fills, but drawn over the flag. Where the artwork ends inside the
      frame (a zoomed-out window, or the clip rectangle of a layer) and its
      field is drawn as stacked shapes, each shape's antialiased edge lets
      the one under it show through as a thin seam. A cover 12 units wide
      centered on the edge, in the color the field has there, hides it at
      44 pixels and up (validate.py --render finds seams that remain).
  "layers": [{"from": [x, y, width, height], "to": [x, y, width, height]}, ...]
      Instead of one window, copy regions of the flag (flag units) into
      rectangles of the output (512 units), each clipped to its rectangle.
      This rebuilds ensigns with the canton drawn as the repo's au-nsw
      draws it (in the circle, the jack's center near the top left and its
      lower-right quarter filling the top-left quadrant; in the square, the
      whole jack in that quadrant) and the badge centered on the right
      half, Canadian pales (side bars and a centered emblem, as in
      circle/countries/ca) and emblems moved to the middle of a field.
      A layer is scaled uniformly unless it sets "stretch": true, which
      fits a 2:1 piece of a Union Jack into a square, so that its
      diagonals run corner to corner as in au-nsw.
  "border": true | false
      Force the grey rim on or off. By default it is added when white covers
      more than 1% of the outer 8 pixels, as the README describes.
  "square": {...}
      Keys that apply to the square variant only.

The circle variant clips with <circle> (clip id "c"), the square variant with
<rect> (clip id "r"). Flag content ids are prefixed with the flag code, so
they cannot collide with these.

Usage: build_variants.py [CODE or COUNTRY ...]
"""

import math
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from lxml import etree

import svgtools as st
from common import REPO, cleaned_path, load_flags, render, run_svgo, select_codes

SIZE = 512
BORDER = {
    "circle": '<!-- border --><circle cx="256" cy="256" r="256" fill="none" stroke="#cdcfd3" stroke-width="16"/>',
    "square": '<!-- border --><rect width="512" height="512" fill="none" stroke="#cdcfd3" stroke-width="16"/>',
}
CLIP = {
    "circle": ("c", '<circle cx="256" cy="256" r="256"/>'),
    "square": ("r", '<rect width="512" height="512"/>'),
}


def window_for(layout, width, height):
    """The square window [x, y, side] in flag units for a single-window layout."""
    unit = min(width, height)
    w, h = width / unit, height / unit
    if "window" in layout:
        x, y, side = layout["window"]
    elif "fit" in layout:
        # Center on an emblem measured with measure.py and size the window
        # so the emblem's longer side spans the given share of the diameter.
        fx, fy, fw, fh = layout["fit"]
        side = max(fw, fh) / layout.get("fill", 0.85)
        x, y = fx + fw / 2 - side / 2, fy + fh / 2 - side / 2
    else:
        crop = layout.get("crop", "center")
        side = 1.0
        x = {"hoist": 0.0, "fly": w - 1.0}.get(crop, (w - 1.0) / 2)
        y = {"top": 0.0, "bottom": h - 1.0}.get(crop, (h - 1.0) / 2)
    zoom = layout.get("zoom", 1.0)
    if zoom != 1.0:
        grown = side / zoom
        x, y, side = x - (grown - side) / 2, y - (grown - side) / 2, grown
    return [x, y, side]


def layers_for(layout, width, height):
    """[(from, to, stretch)] for every layer of a layout."""
    if "layers" in layout:
        return [(layer["from"], layer["to"], layer.get("stretch", False)) for layer in layout["layers"]]
    x, y, side = window_for(layout, width, height)
    return [([x, y, side, side], [0, 0, SIZE, SIZE], False)]


def matrix_for(src, dst, origin, unit, stretch=False):
    """Map a flag-unit rectangle onto an output rectangle."""
    sx, sy, sw, sh = (v * unit for v in src)
    dx, dy, dw, dh = dst
    scale_x = dw / sw
    scale_y = dh / sh if stretch else scale_x
    # Unless the layer asks to be stretched, the height only has to agree
    # to rounding; the width sets the scale.
    if not stretch and abs(scale_x - dh / sh) > 0.01 * scale_x:
        raise ValueError(f"layer {src} -> {dst} would stretch the art")
    return (scale_x, 0, 0, scale_y, dx - (origin[0] + sx) * scale_x, dy - (origin[1] + sy) * scale_y)


def serialize(el):
    text = etree.tostring(el, encoding="unicode", with_tail=False)
    # lxml repeats the namespace on every detached element; the output root
    # declares it once.
    return text.replace(f' xmlns="{st.SVG_NS}"', "")


def compose(code, variant, layout, art, border):
    root = etree.fromstring(art.encode())
    vb = st.viewbox(root)
    unit = min(vb[2], vb[3])
    defs = [child for child in root if st.local(child) == "defs"]
    content = [child for child in root if st.local(child) != "defs" and isinstance(child.tag, str)]
    inherited = {k: v for k, v in root.attrib.items() if k in st.PRESENTATION_ATTRS}

    clip_id, clip_shape = CLIP[variant]
    extra_defs = []
    body = []
    for color, x, y, w, h in layout.get("fills", []):
        body.append(f'<path fill="{st.normalize_color(color)}" d="M{st.fmt(x)} {st.fmt(y)}h{st.fmt(w)}v{st.fmt(h)}H{st.fmt(x)}z"/>')
    layers = layers_for(layout, vb[2], vb[3])
    for index, (src, dst, stretch) in enumerate(layers, start=1):
        group = etree.Element(st.svg_tag("g"), nsmap={None: st.SVG_NS})
        for key, value in inherited.items():
            group.set(key, value)
        group.set("transform", st.matrix_string(*matrix_for(src, dst, vb[:2], unit, stretch)))
        for child in content:
            group.append(deepcopy(child))
        drawn = serialize(group)
        if dst != [0, 0, SIZE, SIZE]:
            layer_id = f"{code}-layer{index}"
            x, y, w, h = dst
            extra_defs.append(f'<clipPath id="{layer_id}"><rect x="{st.fmt(x)}" y="{st.fmt(y)}" '
                              f'width="{st.fmt(w)}" height="{st.fmt(h)}"/></clipPath>')
            drawn = f'<g clip-path="url(#{layer_id})">{drawn}</g>'
        body.append(drawn)
    for color, x, y, w, h in layout.get("covers", []):
        body.append(f'<path fill="{st.normalize_color(color)}" d="M{st.fmt(x)} {st.fmt(y)}h{st.fmt(w)}v{st.fmt(h)}H{st.fmt(x)}z"/>')
    if border:
        body.append(BORDER[variant])

    inner_defs = "".join(serialize(child) for d in defs for child in d if isinstance(child.tag, str))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">',
        "  <defs>",
        f'    <clipPath id="{clip_id}">',
        f"      {clip_shape}",
        "    </clipPath>",
    ]
    lines += [f"    {d}" for d in extra_defs]
    if inner_defs:
        lines.append(f"    {inner_defs}")
    lines += ["  </defs>", f'  <g clip-path="url(#{clip_id})">']
    lines += [f"    {b}" for b in body]
    lines += ["  </g>", "</svg>", ""]
    return "\n".join(lines)


def white_on_rim(svg_text, variant):
    """Share of the outer 8 pixels that is white (all channels >= 0xF0)."""
    image = render(svg_text.encode(), SIZE, SIZE)
    px = image.load()
    total = white = 0
    for y in range(SIZE):
        for x in range(SIZE):
            if variant == "circle":
                distance = ((x + 0.5 - 256) ** 2 + (y + 0.5 - 256) ** 2) ** 0.5
                on_rim = 248 <= distance <= 255.5
            else:
                on_rim = min(x, y, SIZE - 1 - x, SIZE - 1 - y) < 8
            if not on_rim:
                continue
            r, g, b, a = px[x, y]
            total += 1
            if a >= 128 and min(r, g, b) >= 0xF0:
                white += 1
    return white / total


def art_for(code, layout, tmp):
    """The full-size art, re-rounded for a 512-pixel drawing.

    full-size keeps enough decimals for any print size; at 512 pixels half an
    output unit is plenty, which keeps detailed coats of arms within the size
    budget of the circle and square variants.
    """
    source = cleaned_path(code)
    root = etree.parse(str(source)).getroot()
    vb = st.viewbox(root)
    unit = min(vb[2], vb[3])
    scale = max(max(dst[2] / (src[2] * unit), dst[3] / (src[3] * unit))
                for src, dst, _ in layers_for(layout, vb[2], vb[3]))
    scale *= st.largest_local_scale(root)
    precision = max(0, min(8, math.ceil(math.log10(scale / 0.5))))
    out = Path(tmp) / f"{code}.{precision}.svg"
    if not out.exists():
        run_svgo([{"in": str(source), "out": str(out), "pass": "final", "precision": precision}])
    art = etree.fromstring(out.read_bytes())
    st.normalize_colors(art)
    st.explicit_black(art)
    return etree.tostring(art, encoding="unicode")


def layout_for(recipe, variant):
    """The layout of one variant: the recipe's, with its "square" keys
    applied for the square variant."""
    layout = dict(recipe.get("layout", {}))
    square_only = layout.pop("square", {})
    if variant == "square":
        layout.update(square_only)
    return layout


def art_edges(layout, width, height):
    """Lines in the output where the flag's artwork ends inside the frame.

    Returns [(axis, position, start, end)]: axis "x" for a vertical line at
    x = position running from y = start to y = end, "y" for a horizontal
    one. These are where antialiased edges of the artwork meet the fills
    under it, which is where seams can appear.
    """
    unit = min(width, height)
    w, h = width / unit, height / unit
    edges = []
    for src, dst, stretch in layers_for(layout, width, height):
        sx = dst[2] / src[2]
        sy = dst[3] / src[3] if stretch else sx
        # The flag's own outline and the layer's clip rectangle both cut the
        # artwork; the visible artwork is their intersection.
        left = max(dst[0], dst[0] + (0 - src[0]) * sx)
        right = min(dst[0] + dst[2], dst[0] + (w - src[0]) * sx)
        top = max(dst[1], dst[1] + (0 - src[1]) * sy)
        bottom = min(dst[1] + dst[3], dst[1] + (h - src[1]) * sy)
        for position in (left, right):
            if 0.5 < position < SIZE - 0.5:
                edges.append(("x", position, max(top, 0), min(bottom, SIZE)))
        for position in (top, bottom):
            if 0.5 < position < SIZE - 0.5:
                edges.append(("y", position, max(left, 0), min(right, SIZE)))
    return edges


def build(code, recipe, tmp):
    results = {}
    if recipe.get("full_size_only"):
        return results
    for variant in ("circle", "square"):
        layout = layout_for(recipe, variant)
        art = art_for(code, layout, tmp)
        border = layout.get("border")
        if border is None:
            border = white_on_rim(compose(code, variant, layout, art, False), variant) > 0.01
        text = compose(code, variant, layout, art, border)
        out = REPO / variant / "states" / f"{code}.svg"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        results[variant] = (len(text.encode()), border)
    return results


def main():
    flags = load_flags()["flags"]
    codes = [c for c in select_codes(sys.argv[1:], flags) if cleaned_path(c).exists()]
    with tempfile.TemporaryDirectory() as tmp:
        for code in codes:
            results = build(code, flags[code], tmp)
            summary = "  ".join(f"{v} {size:>7} bytes{' +border' if border else ''}"
                                for v, (size, border) in results.items())
            print(f"{code:7} {summary}")


if __name__ == "__main__":
    main()
