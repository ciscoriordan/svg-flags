"""SVG tree helpers shared by clean.py and build_variants.py.

Works on lxml trees. The goal is SVG that CoreSVG (the renderer behind Xcode
asset catalogs, UIImage and SDWebImageSVGCoder) draws the same way browsers
do, which in practice means: no <use>, <mask>, <marker>, <style>, class,
<text> or <image>, and every reference resolved by a plain id.
"""

import math
import re
from copy import deepcopy

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
HREF_ATTRS = ("href", f"{{{XLINK_NS}}}href")

# Elements that are only ever drawn through a reference. Their position in the
# tree does not affect rendering (they are evaluated in the user space of the
# element that references them), so they can all live in one top-level <defs>.
PAINT_SERVERS_AND_CLIPS = {"linearGradient", "radialGradient", "clipPath", "pattern", "filter", "mask", "marker"}
COLOR_ATTRS = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")
GRADIENT_ATTRS = ("gradientUnits", "gradientTransform", "spreadMethod", "x1", "y1", "x2", "y2",
                  "cx", "cy", "r", "fx", "fy", "fr")
# Inherited presentation attributes that may sit on the root <svg> element.
PRESENTATION_ATTRS = {
    "fill", "fill-opacity", "fill-rule", "stroke", "stroke-width", "stroke-opacity", "stroke-linecap",
    "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "clip-rule",
    "opacity", "color", "font-family", "font-size", "font-weight", "visibility",
}
UNIT_SCALE = {"px": 1.0, "pt": 4 / 3, "pc": 16.0, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96.0}
LENGTH = re.compile(r"^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(%|px|pt|pc|mm|cm|in)?\s*$")
URL_REF = re.compile(r"url\(\s*['\"]?#([^)'\"\s]+)['\"]?\s*\)")


def local(el):
    return etree.QName(el).localname if isinstance(el.tag, str) else None


def svg_tag(name):
    return f"{{{SVG_NS}}}{name}"


def href_of(el):
    for attr in HREF_ATTRS:
        value = el.get(attr)
        if value is not None:
            return value
    return None


def drop_href(el):
    for attr in HREF_ATTRS:
        el.attrib.pop(attr, None)


def fmt(value):
    """Format a number compactly for an attribute."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def parse_length(value, reference=None):
    """Resolve an SVG length to user units; percentages need a reference size."""
    m = LENGTH.match(value or "")
    if not m:
        return None
    number, unit = float(m.group(1)), m.group(2)
    if unit == "%":
        return None if reference is None else number / 100 * reference
    return number * UNIT_SCALE.get(unit or "px", 1.0)


def viewbox(root):
    values = [float(v) for v in re.split(r"[\s,]+", root.get("viewBox", "").strip()) if v]
    return values if len(values) == 4 else None


def matrix_string(a, b, c, d, e, f):
    return "matrix(" + " ".join(fmt(v) for v in (a, b, c, d, e, f)) + ")"


TRANSFORM_PART = re.compile(r"(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)")


def multiply(m, n):
    """Compose two affine matrices given as (a, b, c, d, e, f): m then n."""
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def parse_transform(text):
    """Parse an SVG transform list into one affine matrix."""
    result = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, raw in TRANSFORM_PART.findall(text or ""):
        v = [float(x) for x in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", raw)]
        if name == "matrix":
            m = tuple(v[:6])
        elif name == "translate":
            m = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            m = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            angle = math.radians(v[0])
            cos, sin = math.cos(angle), math.sin(angle)
            m = (cos, sin, -sin, cos, 0, 0)
            if len(v) == 3:
                m = multiply(multiply((1, 0, 0, 1, v[1], v[2]), m), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "skewX":
            m = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        else:
            m = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        result = multiply(result, m)
    return result


def largest_local_scale(root):
    """The largest magnification any drawn element sees from its transforms.

    svgo rounds coordinates to a fixed number of decimals in each element's
    own coordinate system, so an element inside a group scaled up 100 times
    needs two more decimals than one drawn at the root.
    """
    largest = 1.0

    def walk(el, matrix):
        nonlocal largest
        if not isinstance(el.tag, str):
            return
        if el.get("transform"):
            matrix = multiply(matrix, parse_transform(el.get("transform")))
        a, b, c, d = matrix[:4]
        largest = max(largest, math.sqrt(abs(a * d - b * c)))
        for child in el:
            walk(child, matrix)

    walk(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return largest


# ---------------------------------------------------------------- structure

def unwrap(el):
    """Replace an element by its children, keeping document order."""
    parent = el.getparent()
    index = parent.index(el)
    for offset, child in enumerate(list(el)):
        parent.insert(index + offset, child)
    parent.remove(el)


def hoist_defs(root):
    """Move every gradient, clip path, pattern, filter, mask and marker into a
    single top-level <defs>, and drop the now-empty <defs> elements."""
    defs = etree.Element(svg_tag("defs"))
    for el in list(root.iter()):
        if local(el) in PAINT_SERVERS_AND_CLIPS and el.getparent() is not None:
            ancestor = el.getparent()
            nested = False
            while ancestor is not None:
                if local(ancestor) in PAINT_SERVERS_AND_CLIPS:
                    nested = True
                    break
                ancestor = ancestor.getparent()
            if not nested:
                defs.append(el)
    for old in list(root.iter(svg_tag("defs"))):
        if len(old) == 0:
            old.getparent().remove(old)
    if len(defs):
        root.insert(0, defs)
    return defs


def resolve_gradient_hrefs(root):
    """Copy inherited stops and attributes into gradients that reference
    another gradient, then drop the reference (CoreSVG ignores it)."""
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}

    def chain(el, seen):
        target = href_of(el)
        if not target or not target.startswith("#"):
            return []
        parent = by_id.get(target[1:])
        if parent is None or parent in seen:
            return []
        return [parent] + chain(parent, seen | {parent})

    for el in list(root.iter()):
        if local(el) not in ("linearGradient", "radialGradient"):
            continue
        ancestors = chain(el, {el})
        if not ancestors and not href_of(el):
            continue
        has_stops = any(local(c) == "stop" for c in el)
        for parent in ancestors:
            if not has_stops and any(local(c) == "stop" for c in parent):
                for stop in parent:
                    if local(stop) == "stop":
                        el.append(deepcopy(stop))
                has_stops = True
            for attr in GRADIENT_ATTRS:
                if el.get(attr) is None and parent.get(attr) is not None:
                    # Linear and radial gradients only share the generic
                    # attributes; geometry does not carry across types.
                    if local(parent) != local(el) and attr not in ("gradientUnits", "gradientTransform", "spreadMethod"):
                        continue
                    el.set(attr, parent.get(attr))
        drop_href(el)


def expand_uses(root):
    """Replace every <use> with a group holding a copy of what it references.

    The copy inherits presentation attributes from the <use>, which is why
    they move onto the wrapper group. The use's x/y become a translation
    applied after its own transform, as the SVG specification defines.
    """
    for _ in range(50):
        uses = [el for el in root.iter() if local(el) == "use"]
        if not uses:
            return
        by_id = {el.get("id"): el for el in root.iter() if el.get("id")}
        for use in uses:
            target = href_of(use) or ""
            source = by_id.get(target[1:]) if target.startswith("#") else None
            group = etree.Element(svg_tag("g"))
            transforms = []
            if use.get("transform"):
                transforms.append(use.get("transform"))
            x = parse_length(use.get("x", "0")) or 0
            y = parse_length(use.get("y", "0")) or 0
            if x or y:
                transforms.append(f"translate({fmt(x)} {fmt(y)})")
            if transforms:
                group.set("transform", " ".join(transforms))
            for attr, value in use.attrib.items():
                name = etree.QName(attr).localname
                if name in ("x", "y", "width", "height", "transform", "href", "id"):
                    continue
                group.set(attr, value)
            clone = None
            if source is not None:
                clone = deepcopy(source)
                if local(clone) == "symbol":
                    clone.tag = svg_tag("g")
                    for attr in ("viewBox", "preserveAspectRatio", "width", "height", "x", "y"):
                        clone.attrib.pop(attr, None)
                for el in clone.iter():
                    if isinstance(el.tag, str):
                        el.attrib.pop("id", None)
            parent = use.getparent()
            if local(parent) == "clipPath":
                # A clip path may only hold shapes, so the copy cannot be
                # wrapped in a group; carry the transforms on each shape.
                shapes = clip_shapes(clone, group.get("transform", "")) if clone is not None else []
                index = parent.index(use)
                parent.remove(use)
                for offset, shape in enumerate(shapes):
                    for attr in ("clip-rule",):
                        if use.get(attr) and shape.get(attr) is None:
                            shape.set(attr, use.get(attr))
                    parent.insert(index + offset, shape)
                continue
            if clone is not None:
                group.append(clone)
            group.tail = use.tail
            parent.replace(use, group)
    raise RuntimeError("<use> references nest more than 50 levels deep")


SHAPES = {"path", "rect", "circle", "ellipse", "line", "polygon", "polyline"}


def clip_shapes(el, transform):
    """Flatten a copied subtree into shapes that carry their full transform."""
    own = " ".join(t for t in (transform, el.get("transform", "")) if t)
    if local(el) in SHAPES:
        if own:
            el.set("transform", own)
        return [el]
    shapes = []
    for child in el:
        if isinstance(child.tag, str):
            shapes.extend(clip_shapes(child, own))
    return shapes


PATH_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
PATH_ARGS = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "s": 4, "q": 4, "t": 2, "a": 7, "z": 0}


def path_vertices(d):
    """Return the vertices of a path, which is where markers are drawn."""
    tokens = PATH_TOKEN.findall(d or "")
    vertices, x, y, sx, sy = [], 0.0, 0.0, 0.0, 0.0
    cmd, i = None, 0
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "zZ":
                x, y = sx, sy
                vertices.append((x, y))
                continue
        lower = cmd.lower()
        count = PATH_ARGS[lower]
        args = [float(v) for v in tokens[i:i + count]]
        i += count
        relative = cmd.islower()
        if lower == "h":
            x = x + args[0] if relative else args[0]
        elif lower == "v":
            y = y + args[0] if relative else args[0]
        else:
            x, y = (x + args[-2], y + args[-1]) if relative else (args[-2], args[-1])
        if lower == "m":
            sx, sy = x, y
            cmd = "l" if relative else "L"
        vertices.append((x, y))
    return vertices


def path_commands(d):
    """Parse path data into absolute commands [(letter, [numbers])].

    Relative commands become absolute, implicit repeats become explicit and
    H and V become L, so every command carries full coordinates.
    """
    tokens = PATH_TOKEN.findall(d or "")
    out, x, y, sx, sy = [], 0.0, 0.0, 0.0, 0.0
    cmd, i = None, 0
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "zZ":
                out.append(("Z", []))
                x, y = sx, sy
                continue
        lower = cmd.lower()
        count = PATH_ARGS[lower]
        args = [float(v) for v in tokens[i:i + count]]
        i += count
        rel = cmd.islower()
        if lower == "h":
            x = x + args[0] if rel else args[0]
            out.append(("L", [x, y]))
        elif lower == "v":
            y = y + args[0] if rel else args[0]
            out.append(("L", [x, y]))
        elif lower == "a":
            ex, ey = (x + args[5], y + args[6]) if rel else (args[5], args[6])
            out.append(("A", args[:5] + [ex, ey]))
            x, y = ex, ey
        else:
            points = [(args[k] + (x if rel else 0), args[k + 1] + (y if rel else 0)) for k in range(0, count, 2)]
            out.append((cmd.upper(), [v for pt in points for v in pt]))
            x, y = points[-1]
        if lower == "m":
            sx, sy = x, y
            cmd = "l" if rel else "L"
    return out


def transform_path(d, m):
    """Apply the affine matrix m to path data and return absolute path data.

    Arcs are only supported under a uniform scale with rotation, which keeps
    them circular or elliptical arcs with scaled radii.
    """
    a, b, c, dd, e, f = m

    def point(px, py):
        return a * px + c * py + e, b * px + dd * py + f

    scale = math.sqrt(abs(a * dd - b * c))
    # Uniform up to rounding: equal axis lengths and perpendicular axes.
    uniform = (abs(math.hypot(a, b) - math.hypot(c, dd)) <= 1e-4 * scale
               and abs(a * c + b * dd) <= 1e-4 * scale * scale)
    flipped = a * dd - b * c < 0
    parts = []
    for letter, args in path_commands(d):
        if letter == "Z":
            parts.append("Z")
        elif letter == "A":
            if not uniform:
                raise RuntimeError("cannot bake a non-uniform transform into an arc")
            rx, ry, rotation, large, sweep, ex, ey = args
            angle = rotation + math.degrees(math.atan2(b, a))
            nx, ny = point(ex, ey)
            parts.append("A" + " ".join(fmt8(v) for v in (rx * scale, ry * scale, angle, large,
                                                           (1 - sweep) if flipped else sweep, nx, ny)))
        else:
            coords = []
            for k in range(0, len(args), 2):
                coords += point(args[k], args[k + 1])
            parts.append(letter + " ".join(fmt8(v) for v in coords))
    return "".join(parts)


def fmt8(value):
    """Format a number with enough significant digits to survive baking a
    transform; the final svgo pass rounds it to the file's precision."""
    text = f"{value:.10g}"
    return "0" if text in ("-0", "0") else text


SHAPE_TO_PATH = {
    "polygon": lambda el: "M" + el.get("points", "").strip() + "Z",
    "polyline": lambda el: "M" + el.get("points", "").strip(),
    "line": lambda el: "M{} {}L{} {}".format(*(el.get(k, "0") for k in ("x1", "y1", "x2", "y2"))),
}


def bake_extreme_transforms(root, low=1e-3, high=1e3):
    """Apply transforms with an extreme scale to the coordinates they act on.

    Some Commons files draw in coordinates in the millions and scale them
    down by a factor around 1e-6. librsvg draws no stroke for a path whose
    own transform shrinks it that much, so those outlines vanish once the
    optimizer moves the scale from a group onto each path. Baking the
    transform into the coordinates (and scaling the stroke width to match)
    draws the same shapes in ordinary units.

    A group's extreme transform is first pushed onto its children; groups
    with a clip path, mask or filter keep theirs, since those are evaluated
    in the group's own coordinates. A shape is left alone when it is
    clipped or painted with a gradient or pattern in user space, whose
    coordinates would move with it.
    """
    def extreme(el):
        if not el.get("transform"):
            return False
        m = parse_transform(el.get("transform"))
        scale = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
        return not low <= scale <= high

    changed = True
    while changed:
        changed = False
        for group in [e for e in root.iter() if local(e) == "g" and extreme(e)]:
            if any(group.get(attr) for attr in ("clip-path", "mask", "filter")):
                continue
            outer = group.attrib.pop("transform")
            for child in group:
                if isinstance(child.tag, str):
                    child.set("transform", f"{outer} {child.get('transform', '')}".strip())
            changed = True
    by_id = {e.get("id"): e for e in root.iter() if isinstance(e.tag, str) and e.get("id")}
    baked = 0
    for el in [e for e in root.iter() if local(e) in ("path", "polygon", "polyline", "line") and extreme(e)]:
        if any(local(a) in PAINT_SERVERS_AND_CLIPS for a in el.iterancestors()):
            continue
        if el.get("clip-path") or el.get("mask"):
            continue
        painted_in_user_space = False
        for attr in ("fill", "stroke"):
            ref = URL_REF.search(inherited(el, attr, "") or "")
            server = by_id.get(ref.group(1)) if ref else None
            if server is not None and (server.get("gradientUnits") == "userSpaceOnUse" or local(server) == "pattern"):
                painted_in_user_space = True
        if painted_in_user_space:
            continue
        m = parse_transform(el.get("transform"))
        scale = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
        d = el.get("d") if local(el) == "path" else SHAPE_TO_PATH[local(el)](el)
        for attr in ("points", "x1", "y1", "x2", "y2"):
            el.attrib.pop(attr, None)
        el.tag = svg_tag("path")
        el.set("d", transform_path(d, m))
        del el.attrib["transform"]
        # Stroke widths are lengths in the shape's own coordinates, which
        # just grew or shrank by the scale.
        width = parse_length(inherited(el, "stroke-width", "1")) or 1.0
        el.set("stroke-width", fmt8(width * scale))
        if el.get("stroke-dasharray") and el.get("stroke-dasharray") != "none":
            el.set("stroke-dasharray", " ".join(fmt8(float(v) * scale)
                                                for v in re.split(r"[\s,]+", el.get("stroke-dasharray").strip())))
        baked += 1
    return baked


def inherited(el, attr, default=None):
    while el is not None:
        if el.get(attr) is not None:
            return el.get(attr)
        el = el.getparent()
    return default


def expand_markers(root):
    """Draw marker-start/mid/end as copies of the marker content at each vertex.

    Only what the sources use is supported: markers with orient="0" or
    "auto" on paths, sized by markerUnits and the marker viewBox.
    """
    by_id = {el.get("id"): el for el in root.iter() if el.get("id")}
    for el in list(root.iter()):
        refs = {pos: el.get(f"marker-{pos}") for pos in ("start", "mid", "end") if el.get(f"marker-{pos}")}
        if not refs:
            continue
        if local(el) != "path":
            raise RuntimeError(f"markers on <{local(el)}> are not supported")
        vertices = path_vertices(el.get("d"))
        instances = []
        for pos, ref in refs.items():
            m = URL_REF.search(ref)
            marker = by_id.get(m.group(1)) if m else None
            if marker is None:
                continue
            if pos == "start":
                points = vertices[:1]
            elif pos == "end":
                points = vertices[-1:]
            else:
                points = vertices[1:-1]
            if marker.get("orient") not in (None, "0"):
                raise RuntimeError("only unrotated markers are supported")
            scale = 1.0
            if marker.get("markerUnits", "strokeWidth") == "strokeWidth":
                scale = parse_length(inherited(el, "stroke-width", "1")) or 1.0
            vb = viewbox(marker)
            width = parse_length(marker.get("markerWidth", "3"))
            height = parse_length(marker.get("markerHeight", "3"))
            if vb:
                scale *= min(width / vb[2], height / vb[3])
            ref_x = parse_length(marker.get("refX", "0")) or 0
            ref_y = parse_length(marker.get("refY", "0")) or 0
            for px, py in points:
                group = etree.Element(svg_tag("g"))
                group.set("transform", f"translate({fmt(px)} {fmt(py)}) scale({fmt(scale)}) "
                                       f"translate({fmt(-ref_x)} {fmt(-ref_y)})")
                for child in marker:
                    copy = deepcopy(child)
                    for sub in copy.iter():
                        if isinstance(sub.tag, str):
                            sub.attrib.pop("id", None)
                    group.append(copy)
                instances.append(group)
        for attr in ("marker-start", "marker-mid", "marker-end"):
            el.attrib.pop(attr, None)
        parent = el.getparent()
        index = parent.index(el)
        for offset, group in enumerate(instances, start=1):
            parent.insert(index + offset, group)
    for marker in [e for e in root.iter() if local(e) == "marker"]:
        marker.getparent().remove(marker)


# Directions used to grow a clip shape by a stroke's half-width. Sixteen
# shifted copies stay within 1% of the half-width of the true outline.
GROW_DIRECTIONS = 16


def mask_stroke_growth(shape, mask, alpha):
    """How far the stroke of a mask shape extends the area the mask lets through.

    Returns half the stroke width when the stroke is opaque and counts as
    "let through" (any opaque stroke in an alpha mask, a white one in a
    luminance mask), 0 when there is no visible stroke, and None when the
    stroke cannot be expressed with a clip path (it is partly transparent,
    or it darkens a luminance mask and so cuts into the shape).
    """
    stroke = inherited_in(shape, mask, "stroke", "none")
    width = parse_length(inherited_in(shape, mask, "stroke-width", "1"))
    opacity = float(inherited_in(shape, mask, "stroke-opacity", "1")) * float(shape.get("opacity", "1"))
    if stroke in (None, "none") or not width or opacity == 0:
        return 0.0
    if opacity < 1:
        return None
    if alpha and normalize_color(stroke).startswith("#"):
        return width / 2
    if normalize_color(stroke) == "#FFFFFF":
        return width / 2
    return None


def masks_to_clips(root):
    """Replace masks that only cut out a shape with the equivalent clip path.

    CoreSVG ignores <mask>, so masked content would be drawn unmasked. A mask
    made of opaque white shapes (or opaque shapes in an alpha mask) lets
    through exactly the area of those shapes, which a clip path expresses.
    A clip path ignores strokes, so a stroked mask shape is replaced by the
    shape plus copies shifted by half the stroke width in every direction;
    their union is the filled shape grown by its stroke, which is the area
    the stroke adds. Masks with gradients, partial opacity or images, and
    strokes that cut into the shape, are left alone and reported by the
    cleaner.
    """
    converted = set()
    for mask in [e for e in root.iter() if local(e) == "mask"]:
        alpha = mask.get("mask-type") == "alpha"
        copy = deepcopy(mask)
        shapes = clip_shapes(copy, "")
        drawn = [e for e in mask.iter() if isinstance(e.tag, str) and e is not mask]
        if not shapes or any(local(e) not in SHAPES | {"g"} for e in drawn):
            continue
        usable = True
        growth = []
        for shape in shapes:
            fill = normalize_color(inherited_in(shape, copy, "fill", "#000000"))
            opacity = float(shape.get("opacity", "1")) * float(inherited_in(shape, copy, "fill-opacity", "1"))
            if opacity < 1 or not (fill == "#FFFFFF" or (alpha and fill and fill.startswith("#"))):
                usable = False
            grow = mask_stroke_growth(shape, copy, alpha)
            if grow is None:
                usable = False
            growth.append((grow or 0.0, inherited_in(shape, copy, "fill-rule", None)))
        if not usable:
            continue
        clip = etree.Element(svg_tag("clipPath"))
        clip.set("id", mask.get("id"))
        if mask.get("maskContentUnits") == "objectBoundingBox":
            clip.set("clipPathUnits", "objectBoundingBox")
        for shape, (grow, fill_rule) in zip(shapes, growth):
            for attr in ("fill", "fill-rule", "stroke", "stroke-width", "stroke-opacity", "opacity",
                         "fill-opacity", "style"):
                shape.attrib.pop(attr, None)
            if fill_rule:
                shape.set("clip-rule", fill_rule)
            clip.append(shape)
            for k in range(GROW_DIRECTIONS if grow else 0):
                angle = 2 * math.pi * k / GROW_DIRECTIONS
                shifted = deepcopy(shape)
                # The stroke width is measured in the shape's own coordinates,
                # so the shift goes innermost, after the shape's transform.
                shift = f"translate({fmt(grow * math.cos(angle))} {fmt(grow * math.sin(angle))})"
                shifted.set("transform", f"{shape.get('transform', '')} {shift}".strip())
                clip.append(shifted)
        mask.getparent().replace(mask, clip)
        converted.add(mask.get("id"))
    for el in root.iter():
        if not isinstance(el.tag, str) or not el.get("mask"):
            continue
        m = URL_REF.search(el.get("mask"))
        if not m or m.group(1) not in converted:
            continue
        del el.attrib["mask"]
        if el.get("clip-path"):
            # Both a clip and a mask: clip the element, then clip a wrapper.
            wrapper = etree.Element(svg_tag("g"))
            wrapper.set("clip-path", f"url(#{m.group(1)})")
            el.getparent().replace(el, wrapper)
            wrapper.append(el)
        else:
            el.set("clip-path", f"url(#{m.group(1)})")
    return converted


def flatten_images(root):
    """Replace embedded raster images with a rectangle of their median color.

    Some Commons coats of arms carry small JPEG patches, rasterized shading
    from an illustration program, inside clip paths. CoreSVG cannot draw
    embedded images reliably and the repo keeps flags fully vector, so each
    patch becomes a flat rectangle in the same place, under the same clip.
    Near-white pixels are left out of the median: JPEG has no transparency,
    so the parts of a patch that its clip path hides are stored as white.
    """
    import base64
    import io
    from statistics import median

    from PIL import Image

    count = 0
    for image in [e for e in root.iter() if local(e) == "image"]:
        href = href_of(image) or ""
        m = re.match(r"data:image/[a-z]+;base64,(.*)", href, re.S)
        if not m:
            raise RuntimeError("an <image> refers to an external file")
        pixels = list(Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB").getdata())
        colored = [p for p in pixels if min(p) < 245] or pixels
        color = "#" + "".join(f"{int(median(p[i] for p in colored)):02X}" for i in range(3))
        rect = etree.Element(svg_tag("rect"))
        for attr in ("x", "y", "width", "height", "transform", "clip-path", "opacity"):
            if image.get(attr) is not None:
                rect.set(attr, image.get(attr))
        rect.set("fill", color)
        rect.tail = image.tail
        image.getparent().replace(image, rect)
        count += 1
    return count


def drop_blurred(root):
    """Remove elements drawn through a Gaussian blur, and the filters.

    Some drawings add soft shadows and highlights as blurred shapes.
    CoreSVG cannot apply filters and would draw them as hard-edged blots,
    which looks worse than leaving the soft shading out.
    """
    blur_only = {e.get("id") for e in root.iter() if local(e) == "filter"
                 and all(local(c) == "feGaussianBlur" for c in e if isinstance(c.tag, str))}
    removed = 0
    for el in [e for e in root.iter() if isinstance(e.tag, str) and e.get("filter")]:
        m = URL_REF.search(el.get("filter"))
        if m and m.group(1) in blur_only and el.getparent() is not None:
            el.getparent().remove(el)
            removed += 1
    for flt in [e for e in root.iter() if local(e) == "filter" and e.get("id") in blur_only]:
        flt.getparent().remove(flt)
    return removed


def drop_unpainted(root):
    """Remove shapes that paint nothing: no fill and no stroke.

    Editors leave such shapes behind (often carrying a filter or marker of
    their own), and they would otherwise keep features CoreSVG cannot
    draw in the file although nothing of them is visible.
    """
    removed = 0
    for el in [e for e in root.iter() if local(e) in SHAPES]:
        if any(local(a) in PAINT_SERVERS_AND_CLIPS for a in el.iterancestors()):
            continue
        if el.get("marker-start") or el.get("marker-mid") or el.get("marker-end"):
            continue
        if inherited(el, "fill", "#000000") == "none" and inherited(el, "stroke", "none") == "none":
            el.getparent().remove(el)
            removed += 1
    for flt in [e for e in root.iter() if local(e) == "filter"]:
        if ("url(#%s)" % flt.get("id")) not in etree.tostring(root, encoding="unicode"):
            flt.getparent().remove(flt)
    return removed


def drop_empty_clips(root):
    """Remove elements clipped by an empty clip path, and the clip paths.

    An empty clip path hides everything it is applied to, and browsers and
    rsvg draw nothing. CoreSVG ignores such a clip and draws the element in
    full, so these invisible leftovers would appear in an app.
    """
    empty = {e.get("id") for e in root.iter()
             if local(e) == "clipPath" and not any(local(c) in SHAPES | {"use", "text"} for c in e.iter())}
    removed = 0
    for el in [e for e in root.iter() if isinstance(e.tag, str) and e.get("clip-path")]:
        m = URL_REF.search(el.get("clip-path"))
        if m and m.group(1) in empty and el.getparent() is not None:
            el.getparent().remove(el)
            removed += 1
    for clip in [e for e in root.iter() if local(e) == "clipPath" and e.get("id") in empty]:
        clip.getparent().remove(clip)
    return removed


def group_shared_clips(root):
    """Wrap runs of siblings that share a clip path and transform in one group.

    Illustrator exports often repeat the same clip-path and transform on
    hundreds of consecutive shapes (one per strip of a blended gradient).
    Clipping the group instead draws the same pixels with far fewer bytes.
    """
    for parent in [e for e in root.iter() if local(e) in ("svg", "g")]:
        children = list(parent)
        run = []

        def flush():
            if len(run) > 1:
                group = etree.Element(svg_tag("g"))
                group.set("clip-path", run[0].get("clip-path"))
                if run[0].get("transform"):
                    group.set("transform", run[0].get("transform"))
                parent.insert(parent.index(run[0]), group)
                for el in run:
                    el.attrib.pop("clip-path", None)
                    el.attrib.pop("transform", None)
                    group.append(el)
            run.clear()

        for child in children:
            key = (child.get("clip-path"), child.get("transform")) if isinstance(child.tag, str) else None
            if key is None or key[0] is None or local(child) in PAINT_SERVERS_AND_CLIPS | {"defs"}:
                flush()
                continue
            if run and (run[0].get("clip-path"), run[0].get("transform")) != key:
                flush()
            run.append(child)
        flush()


def inherited_in(el, stop, attr, default):
    """Like inherited(), but only up to (and including) the element `stop`."""
    while el is not None:
        if el.get(attr) is not None:
            return el.get(attr)
        if el is stop:
            break
        el = el.getparent()
    return default


def resolve_lengths(root):
    """Turn %, pt, mm, cm and in lengths on shapes into plain user units.

    CoreSVG does not resolve percentages against the viewBox, so a
    width="100%" background rectangle would otherwise disappear.
    """
    vb = viewbox(root)
    width, height = vb[2], vb[3]
    diagonal = math.sqrt((width * width + height * height) / 2)
    horizontal = {"x", "width", "cx", "rx", "x1", "x2"}
    vertical = {"y", "height", "cy", "ry", "y1", "y2"}
    for el in root.iter():
        name = local(el)
        if name not in ("rect", "circle", "ellipse", "line", "image", "use", "path", "polygon", "polyline", "g"):
            continue
        for attr, value in list(el.attrib.items()):
            m = LENGTH.match(value)
            if not m or not m.group(2):
                continue
            if attr in horizontal:
                resolved = parse_length(value, width)
            elif attr in vertical:
                resolved = parse_length(value, height)
            elif attr in ("r", "stroke-width"):
                resolved = parse_length(value, diagonal)
            else:
                continue
            if resolved is not None:
                el.set(attr, fmt(resolved))


def normalize_color(value):
    """Uppercase 6-digit hex for every plain color; leave url() and keywords."""
    if value is None:
        return value
    v = value.strip()
    m = re.fullmatch(r"#([0-9A-Fa-f]{3})", v)
    if m:
        return "#" + "".join(ch * 2 for ch in m.group(1)).upper()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
        return v.upper()
    m = re.fullmatch(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", v)
    if m:
        return "#" + "".join(f"{min(255, int(c)):02X}" for c in m.groups())
    return value


def normalize_colors(root):
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for attr in COLOR_ATTRS:
            if el.get(attr) is not None:
                el.set(attr, normalize_color(el.get(attr)))


def referenced_ids(root):
    refs = set()
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for attr, value in el.attrib.items():
            refs.update(URL_REF.findall(value))
            if etree.QName(attr).localname == "href" and value.startswith("#"):
                refs.add(value[1:])
    return refs


def prefix_ids(root, prefix):
    """Namespace every referenced id and drop the rest.

    Ids are prefixed with the flag code, so they can never collide with the
    clip path ids ("c", "r") of the circle and square variants. A collision
    of exactly that kind once made CoreSVG drop whole flags.
    """
    refs = referenced_ids(root)
    for el in root.iter():
        if not isinstance(el.tag, str) or el.get("id") is None:
            continue
        if el.get("id") in refs:
            el.set("id", f"{prefix}-{el.get('id')}")
        else:
            del el.attrib["id"]

    def rename(match):
        return f"url(#{prefix}-{match.group(1)})"

    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for attr, value in list(el.attrib.items()):
            if "url(" in value:
                el.set(attr, URL_REF.sub(rename, value))
            elif etree.QName(attr).localname == "href" and value.startswith("#"):
                el.set(attr, f"#{prefix}-{value[1:]}")


def explicit_black(root):
    """Write fill="#000000" on shapes that are black only by default.

    svgo drops fill="#000" because black is the default, but the README lists
    each flag's colors from its fill attributes, so the black must be written.
    """
    for el in root.iter():
        if local(el) not in SHAPES:
            continue
        ancestors, node = [], el
        while node is not None:
            ancestors.append(node)
            node = node.getparent()
        if any(local(a) in PAINT_SERVERS_AND_CLIPS for a in ancestors):
            continue
        if not any(a.get("fill") is not None for a in ancestors):
            el.set("fill", "#000000")


def colors_in(svg_text):
    """Every fill/stroke/stop color, uppercase 6-digit hex, as validators read them."""
    found = set()
    for value in re.findall(r'(?:fill|stroke|stop-color)="(#[0-9A-Fa-f]{3,6})"', svg_text):
        found.add(normalize_color(value))
    return found
