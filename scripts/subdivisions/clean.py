#!/usr/bin/env python3
"""Clean each pinned Commons SVG into full-size/states and full-size-simplified/states.

1. svgo, first pass: inline CSS rules and turn style attributes into
   presentation attributes; drop editor metadata. Path data and transforms
   are left as they are (see svgo_run.mjs).
2. Python: give the root an explicit size and viewBox, resolve percentage and
   physical units, move gradients and clip paths into one <defs>, resolve
   gradient inheritance, expand <use> and markers, turn shape-only masks into
   clip paths, drop content hidden by empty clip paths and shapes that paint
   nothing, apply transforms that scale by a factor beyond 1e-3 or 1e3 to
   the coordinates they act on (librsvg skips strokes under such
   transforms), normalize colors to uppercase 6-digit hex and namespace ids
   with the flag code. Two recipe options ("clean" in flags.json) change the
   artwork on purpose and state why, with their own drift limits:
   "flatten_images" draws embedded raster shading as flat rectangles of its
   median color, and "drop_blurred" leaves out shapes drawn through a
   Gaussian blur, which CoreSVG cannot draw.
   A third recipe option, "canvas", restores proportions the flag's law
   gives when the Commons drawing has others: "extend" grows the viewBox by
   [left, top, right, bottom] user units, and "fills" ([color, x, y, width,
   height] in the same units) continue the field there, drawn under the
   artwork. Its "why" records the law and what was wrong.
3. svgo, final pass: compact the result. The number of decimals starts from
   the size of the drawing and its most magnified transform, and goes up
   until the compacted file renders as faithfully at the check size as one
   rounded to 8 decimals, so rounding cannot thin a line or move a small
   charge.
4. Check that nothing CoreSVG cannot draw is left, and measure how far the
   cleaned file drifts from the Commons original (rendered with rsvg), with
   the same limits validate.py enforces. With "canvas", only the area of
   the original is compared.

full-size-simplified is a copy of full-size, as for every other flag that
does not come from circle-flags or square-flags.

Usage: clean.py [CODE or COUNTRY ...]
"""

import math
import shutil
import sys
import tempfile
from pathlib import Path

from lxml import etree

import svgtools as st
from common import (REPO, check_dimensions, cleaned_path, commons_cache_path, compare_renders, drift_limits,
                    fidelity, load_flags, load_sources, render, run_svgo, select_codes)

FORBIDDEN = {"mask", "use", "marker", "style", "text", "image", "filter", "foreignObject", "script", "symbol", "switch"}
ROOT_KEEP = {"width", "height", "viewBox"}
MAX_PRECISION = 8


def precision_for(viewbox, local_scale):
    """Decimal places that keep rounding below about 1/8192 of the flag width,
    in the most magnified coordinate system the file uses."""
    largest = max(viewbox[2], viewbox[3])
    return max(0, min(MAX_PRECISION, math.ceil(math.log10(8192 / largest * local_scale))))


def apply_style_leftovers(root):
    """svgo keeps style properties it does not know as attributes; turn the
    presentation ones into attributes and drop editor-only ones."""
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        style = el.attrib.pop("style", None)
        if style:
            for declaration in style.split(";"):
                if ":" not in declaration:
                    continue
                prop, value = (part.strip() for part in declaration.split(":", 1))
                if prop in st.PRESENTATION_ATTRS or prop in st.COLOR_ATTRS or prop in ("stop-opacity", "display", "mask-type"):
                    el.set(prop, value)
        el.attrib.pop("class", None)
    for style in [e for e in root.iter() if st.local(e) == "style"]:
        if (style.text or "").strip():
            raise RuntimeError("a <style> block could not be inlined")
        style.getparent().remove(style)


def establish_size(root, source):
    """Return (width, height, viewBox) with the viewBox always present."""
    width = st.parse_length(root.get("width"))
    height = st.parse_length(root.get("height"))
    vb = st.viewbox(root)
    if vb is None:
        vb = [0.0, 0.0, width or source["revision"]["width"], height or source["revision"]["height"]]
    if width is None or height is None:
        # Without an absolute size the drawing takes the viewBox proportions.
        # (Commons then reports a nominal 512-pixel width, whose rounded
        # height would distort the flag slightly.)
        width, height = vb[2], vb[3]
    root.set("viewBox", " ".join(st.fmt(v) for v in vb))
    return width, height, vb


def extend_canvas(root, width, height, vb, canvas):
    """Grow the drawing by canvas["extend"] user units on each side and draw
    canvas["fills"] under the artwork; returns the new (width, height, vb)."""
    left, top, right, bottom = canvas["extend"]
    scale = width / vb[2]
    vb = [vb[0] - left, vb[1] - top, vb[2] + left + right, vb[3] + top + bottom]
    root.set("viewBox", " ".join(st.fmt(v) for v in vb))
    at = max((i + 1 for i, child in enumerate(root) if st.local(child) == "defs"), default=0)
    for offset, (color, x, y, w, h) in enumerate(canvas["fills"]):
        path = etree.Element(st.svg_tag("path"))
        path.set("fill", st.normalize_color(color))
        path.set("d", f"M{st.fmt(x)} {st.fmt(y)}h{st.fmt(w)}v{st.fmt(h)}H{st.fmt(x)}z")
        root.insert(at + offset, path)
    return vb[2] * scale, vb[3] * scale, vb


def clean_tree(root, code, source, options, canvas=None):
    width, height, vb = establish_size(root, source)
    apply_style_leftovers(root)
    for anchor in [e for e in root.iter() if st.local(e) in ("a", "switch")]:
        st.unwrap(anchor)
    # Editor leftovers that draw nothing: metadata, and text elements without
    # any characters (CoreSVG cannot draw text, so real text must be outlined).
    for el in [e for e in root.iter() if st.local(e) in ("title", "desc", "metadata")
               or (st.local(e) == "text" and not "".join(e.itertext()).strip())]:
        el.getparent().remove(el)
    st.resolve_lengths(root)
    st.hoist_defs(root)
    st.resolve_gradient_hrefs(root)
    st.expand_uses(root)
    st.expand_markers(root)
    st.masks_to_clips(root)
    st.drop_empty_clips(root)
    st.drop_unpainted(root)
    if options.get("flatten_images"):
        st.flatten_images(root)
    if options.get("drop_blurred"):
        st.drop_blurred(root)
    st.bake_extreme_transforms(root)
    st.group_shared_clips(root)
    if canvas:
        width, height, vb = extend_canvas(root, width, height, vb, canvas)
    st.normalize_colors(root)
    for attr in list(root.attrib):
        name = etree.QName(attr).localname
        if attr not in ROOT_KEEP and name not in st.PRESENTATION_ATTRS:
            del root.attrib[attr]
    root.set("width", st.fmt(round(width, 2)))
    root.set("height", st.fmt(round(height, 2)))
    st.prefix_ids(root, code)
    return precision_for(vb, st.largest_local_scale(root))


def leftovers(root):
    found = sorted({st.local(e) for e in root.iter() if st.local(e) in FORBIDDEN})
    for el in root.iter():
        if isinstance(el.tag, str) and any(etree.QName(a).localname == "href" for a in el.attrib):
            found.append(f"href on <{st.local(el)}>")
    return found


def finalize(text):
    """Re-check svgo's output: colors uppercase, root attribute order fixed."""
    root = etree.fromstring(text.encode())
    st.normalize_colors(root)
    # svgo can empty a clip path whose shapes collapse to nothing.
    st.drop_empty_clips(root)
    st.explicit_black(root)
    attrs = {k: v for k, v in root.attrib.items()}
    for k in list(root.attrib):
        del root.attrib[k]
    for key in ("width", "height", "viewBox"):
        root.set(key, attrs.pop(key))
    for key, value in attrs.items():
        root.set(key, value)
    etree.cleanup_namespaces(root)
    return etree.tostring(root, encoding="unicode") + "\n"


def compact(code, middle, precision, tmp):
    """Run the final svgo pass at the lowest precision that renders as
    faithfully as the most precise output.

    The starting precision assumes coordinates are spread over the whole
    drawing; thin strokes and small arcs can need more, which only a render
    shows. A few files differ from their uncompacted form by a pixel or two
    at any precision (svgo rewrites some curves as arcs, for example), so the
    goal is the most precise output's result, not zero.
    """
    size = check_dimensions(middle)
    reference = render(middle, *size)

    def attempt(decimals):
        out = tmp / f"{code}.final{decimals}.svg"
        run_svgo([{"in": str(middle), "out": str(out), "pass": "final", "precision": decimals}])
        text = finalize(out.read_text(encoding="utf-8"))
        return text, compare_renders(reference, render(text.encode(), *size))

    best_text, (best_share, best_region) = attempt(MAX_PRECISION)
    for decimals in range(precision, MAX_PRECISION):
        text, (share, region) = attempt(decimals)
        if region <= max(best_region, 1) and share <= max(best_share, 1e-6):
            return text, decimals
    return best_text, MAX_PRECISION


def clean(code, source, recipe, tmp):
    original = commons_cache_path(code)
    if not original.exists():
        raise RuntimeError("source not downloaded; run fetch.py")
    first = tmp / f"{code}.first.svg"
    run_svgo([{"in": str(original), "out": str(first), "pass": "first", "precision": 6}])

    root = etree.parse(str(first), etree.XMLParser(huge_tree=True, remove_comments=True)).getroot()
    precision = clean_tree(root, code, source, recipe.get("clean", {}), recipe.get("canvas"))
    problems = leftovers(root)
    if problems:
        raise RuntimeError("cannot be drawn by CoreSVG after cleaning: " + ", ".join(problems))

    middle = tmp / f"{code}.middle.svg"
    middle.write_text(etree.tostring(root, encoding="unicode"), encoding="utf-8")
    text, precision = compact(code, middle, precision, tmp)

    out = cleaned_path(code)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    simplified = REPO / "full-size-simplified" / "states" / f"{code}.svg"
    simplified.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out, simplified)
    return fidelity(original, out, recipe), precision, len(text.encode())


def main():
    sources = load_sources()
    flags = load_flags()["flags"]
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for code in select_codes(sys.argv[1:], sources):
            try:
                (share, region), precision, size = clean(code, sources[code], flags[code], Path(tmp))
                max_share, max_region = drift_limits(flags[code])
                flag = "" if share <= max_share and region <= max_region else \
                    "   <-- check against the original"
                print(f"{code:7} {size:>8} bytes  {precision} decimals  {share * 100:6.3f}% of pixels differ "
                      f"from Commons, largest patch {region} px{flag}")
            except Exception as error:  # report every flag, then fail
                failures.append(code)
                print(f"{code:7} FAILED: {error}")
    if failures:
        sys.exit(f"{len(failures)} flag(s) failed: {' '.join(failures)}")


if __name__ == "__main__":
    main()
